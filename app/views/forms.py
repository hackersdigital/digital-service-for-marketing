# app/views/forms.py
from flask import Blueprint, render_template, request, abort, g, current_app
from ..models.forms import get_form
from ..models.submissions import insert_submission, update_submission
from ..services.delivery import deliver
from ..auth import require_agent_token

bp = Blueprint("forms", __name__, url_prefix="/f")

# Internal fields that must NOT be stored in payload or sent to client
INTERNAL_FORM_KEYS = {"_agent_token", "agent_uid"}

def _sanitize_form(form_dict: dict) -> dict:
    """Return only public (deliverable) fields."""
    return {
        k: v for k, v in form_dict.items()
        if k not in INTERNAL_FORM_KEYS and not k.startswith("_")
    }

def _validate(cfg, data):
    """Validate required fields using sanitized data."""
    missing = []
    delivery_cfg = (cfg.get("delivery") or {})
    validation = delivery_cfg.get("validation", {})
    reqs = validation.get("required_fields", [])
    for k in reqs:
        if not data.get(k):
            missing.append(k)
    for grp in validation.get("require_any", []):
        if not any(data.get(k) for k in grp):
            missing.append(f"one of {grp}")
    return missing

@bp.get("/<client_slug>/<form_slug>")
def render_form(client_slug, form_slug):
    cfg = get_form(client_slug, form_slug)
    if not cfg:
        abort(404)
    return render_template("form_dynamic.html", form_cfg=cfg)

@bp.post("/<client_slug>/<form_slug>/submit")
def submit_form(client_slug, form_slug):
    # 1) Auth (but do NOT forward/store the token)
    require_agent_token()

    # 2) Load form config
    cfg = get_form(client_slug, form_slug)
    if not cfg:
        abort(404)

    # 3) Raw form data
    raw_form = request.form.to_dict(flat=True)

    # 4) Agent tracking (stored separately, not delivered)
    agent_uid = raw_form.get("agent_uid") or request.headers.get("X-Agent-UID")

    # 5) Sanitize payload (strip internal fields)
    public_form = _sanitize_form(raw_form)

    # 6) Validate using sanitized data
    missing = _validate(cfg, public_form)
    if missing:
        return render_template("result.html", status="error", detail={"missing": missing}), 400

    # 7) Persist submission (payload = sanitized only)
    created_at = g.db.client.admin.command("serverStatus")["localTime"]
    sub_doc = {
        "client_slug": client_slug,
        "form_slug": form_slug,
        "created_at": created_at,
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "ua": request.headers.get("User-Agent", ""),
        "agent": {"uid": agent_uid} if agent_uid else {},
        "payload": public_form,
        "delivery": {"status": "pending", "attempts": 0}
    }
    sub_id = insert_submission(sub_doc)

    # 8) Deliver using ONLY the sanitized form data
    ctx = {"client_ip": sub_doc["ip"]}
    outbound, result = deliver(cfg, public_form, ctx)

    # 9) Log attempt + update submission
    g.db.deliveries.insert_one({
        "submission_id": sub_id,
        "attempted_at": g.db.client.admin.command("serverStatus")["localTime"],
        "request": {
            "url": cfg["delivery"]["url"],
            "headers": cfg["delivery"].get("headers"),
            "body": outbound
        },
        "response": result
    })
    update_submission(sub_id, {
        "delivery.status": result["normalized_status"],
        "delivery.attempts": 1,
        "delivery.last_result": result
    })

    # 10) Show result
    return render_template(
        "result.html", status=result["normalized_status"], detail=result["body"]
    ), (200 if result["normalized_status"] != "error" else 502)
