# app/auth.py
from flask import request, abort, current_app

def _bearer_token_from_header() -> str:
    auth = request.headers.get("Authorization", "")
    # Only accept Bearer; ignore Basic or anything else so ?token= works
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return ""

def require_agent_token():
    token = _bearer_token_from_header()
    if not token:
        token = request.form.get("_agent_token", "")
    if token != (current_app.config.get("AGENT_TOKEN") or "").strip():
        abort(403)

def require_client_token():
    token = _bearer_token_from_header()
    if token != (current_app.config.get("CLIENT_TOKEN") or "").strip():
        abort(403)

def require_portal_token():
    token = (
        _bearer_token_from_header()
        or (request.args.get("token", "") or "").strip()
        or (request.cookies.get("portal_token", "") or "").strip()
    )
    expected = (current_app.config.get("PORTAL_TOKEN") or "").strip()
    if token != expected:
        abort(403)

# from flask import request, abort, current_app

# def require_agent_token():
#     token = request.headers.get("Authorization", "").replace("Bearer ", "") or request.form.get("_agent_token", "")
#     if token != current_app.config.get("AGENT_TOKEN"):
#         abort(403)

# def require_client_token():
#     token = request.headers.get("Authorization", "").replace("Bearer ", "")
#     if token != current_app.config.get("CLIENT_TOKEN"):
#         abort(403)

# def require_portal_token():
#     token = request.headers.get("Authorization", "").replace("Bearer ", "")
#     if not token:
#         token = request.args.get("token", "")
#     if token != current_app.config.get("PORTAL_TOKEN"):
#         abort(403)
