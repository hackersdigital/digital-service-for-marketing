from flask import Blueprint, render_template, request, abort, g, current_app
from ..models.forms import get_form
from ..models.submissions import insert_submission, update_submission
from ..services.delivery import deliver
from ..auth import require_agent_token

bp = Blueprint("forms", __name__, url_prefix="/f")

@bp.get("/<client_slug>/<form_slug>")
def render_form(client_slug, form_slug):
    cfg = get_form(client_slug, form_slug)
    if not cfg:
        abort(404)
    return render_template("form_dynamic.html", form_cfg=cfg)

@bp.post("/<client_slug>/<form_slug>/submit")
def submit_form(client_slug, form_slug):
    require_agent_token()
    cfg = get_form(client_slug, form_slug)
    if not cfg:
        abort(404)

    form_data = request.form.to_dict(flat=True)
    missing = []
    reqs = cfg["delivery"].get("validation", {}).get("required_fields", [])
    for k in reqs:
        if not form_data.get(k): missing.append(k)
    for grp in cfg["delivery"]["validation"].get("require_any", []):
        if not any(form_data.get(k) for k in grp):
            missing.append(f"one of {grp}")
    if missing:
        return render_template("result.html", status="error", detail={"missing": missing}), 400

    doc = {
        "client_slug": client_slug,
        "form_slug": form_slug,
        "created_at": g.db.client.admin.command("serverStatus")["localTime"],
        "ip": request.remote_addr,
        "payload": form_data,
        "delivery": {"status": "pending", "attempts": 0}
    }
    sub_id = insert_submission(doc)

    outbound, result = deliver(cfg, form_data, {"client_ip": request.remote_addr})
    g.db.deliveries.insert_one({
        "submission_id": sub_id,
        "attempted_at": g.db.client.admin.command("serverStatus")["localTime"],
        "request": {"url": cfg["delivery"]["url"], "headers": cfg["delivery"].get("headers"), "body": outbound},
        "response": result
    })
    update_submission(sub_id, {"delivery.status": result["normalized_status"], "delivery.last_result": result})

    return render_template("result.html", status=result["normalized_status"], detail=result["body"]), (
        200 if result["normalized_status"] != "error" else 502
    )
