# app/services/delivery.py
import time, requests
from flask import current_app
from .templating import render_mapping, deep_get

def _strip_internal(d: dict) -> dict:
    return {k: v for k, v in (d or {}).items() if not k.startswith("_")}

def deliver(form_cfg, form_data, ctx):
    # sanitize inputs (never send internal fields)
    safe_form = _strip_internal(form_data)

    envvars = {
        "LP_CAMPAIGN_ID": current_app.config.get("LP_CAMPAIGN_ID"),
        "LP_SUPPLIER_ID": current_app.config.get("LP_SUPPLIER_ID"),
        "LP_KEY": current_app.config.get("LP_KEY"),
    }

    # render mapping -> outbound payload
    payload = render_mapping(form_cfg["delivery"]["mapping"], safe_form, envvars, ctx)

    # BACKFILL: if mapping forgot these, inject from env
    def _blank(x): return x is None or x == "" or x == "None"
    if envvars.get("LP_CAMPAIGN_ID") and _blank(payload.get("lp_campaign_id")):
        payload["lp_campaign_id"] = envvars["LP_CAMPAIGN_ID"]
    if envvars.get("LP_SUPPLIER_ID") and _blank(payload.get("lp_supplier_id")):
        payload["lp_supplier_id"] = envvars["LP_SUPPLIER_ID"]
    if envvars.get("LP_KEY") and _blank(payload.get("lp_key")):
        payload["lp_key"] = envvars["LP_KEY"]

    headers = form_cfg["delivery"].get("headers", {})
    as_json = "application/json" in headers.get("Content-Type", "").lower()
    url = form_cfg["delivery"]["url"]

    t0 = time.time()
    resp = requests.post(
        url,
        json=payload if as_json else None,
        data=None if as_json else payload,
        headers=headers,
        timeout=15,
    )
    latency = int((time.time() - t0) * 1000)

    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text}

    path = form_cfg["delivery"]["response"].get("path", "status")
    val = str(deep_get(body, path, "ERROR")).upper()
    succ = set(map(str.upper, form_cfg["delivery"]["response"].get("success_values", [])))
    dup  = set(map(str.upper, form_cfg["delivery"]["response"].get("duplicate_values", [])))
    norm = "delivered" if val in succ else "duplicated" if val in dup else "error"

    return payload, {
        "http_status": resp.status_code,
        "latency_ms": latency,
        "body": body,
        "value": val,
        "normalized_status": norm,
    }
