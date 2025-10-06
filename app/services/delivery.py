import time, requests
from flask import current_app
from .templating import render_mapping, deep_get

def deliver(form_cfg, form_data, ctx):
    envvars = {
        "LP_CAMPAIGN_ID": current_app.config.get("LP_CAMPAIGN_ID"),
        "LP_SUPPLIER_ID": current_app.config.get("LP_SUPPLIER_ID"),
        "LP_KEY": current_app.config.get("LP_KEY")
    }
    payload = render_mapping(form_cfg["delivery"]["mapping"], form_data, envvars, ctx)
    headers = form_cfg["delivery"].get("headers", {})
    as_json = "application/json" in headers.get("Content-Type", "").lower()
    url = form_cfg["delivery"]["url"]

    t0 = time.time()
    resp = requests.post(url, json=payload if as_json else None,
                              data=None if as_json else payload,
                              headers=headers, timeout=15)
    latency = int((time.time() - t0) * 1000)

    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text}

    path = form_cfg["delivery"]["response"].get("path", "status")
    val = str(deep_get(body, path, "ERROR")).upper()

    succ = set(map(str.upper, form_cfg["delivery"]["response"].get("success_values", [])))
    dup = set(map(str.upper, form_cfg["delivery"]["response"].get("duplicate_values", [])))

    norm = "delivered" if val in succ else "duplicated" if val in dup else "error"
    return payload, {
        "http_status": resp.status_code,
        "latency_ms": latency,
        "body": body,
        "value": val,
        "normalized_status": norm
    }
