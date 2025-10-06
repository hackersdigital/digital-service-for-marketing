# app/auth.py
from flask import request, abort, current_app

def _bearer_token_from_header() -> str:
    """Return Bearer token from Authorization header, or '' if not present/unsupported."""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return ""

def require_agent_token():
    """
    Allow form submissions if ANY of the following are present and match:
      - Authorization: Bearer <AGENT_TOKEN>
      - form field _agent_token=<AGENT_TOKEN>  (legacy; optional to keep)
      - ?token=<PORTAL_TOKEN>
      - cookie portal_token=<PORTAL_TOKEN>     (set by visiting /portal?token=...)
    """
    token = (
        _bearer_token_from_header()
        or (request.form.get("_agent_token", "") or "").strip()
        or (request.args.get("token", "") or "").strip()
        or (request.cookies.get("portal_token", "") or "").strip()
    )
    agent_expected  = (current_app.config.get("AGENT_TOKEN") or "").strip()
    portal_expected = (current_app.config.get("PORTAL_TOKEN") or "").strip()

    if token not in {agent_expected, portal_expected}:
        abort(403)

def require_client_token():
    """For client webhooks: must provide Authorization: Bearer <CLIENT_TOKEN>."""
    token = _bearer_token_from_header()
    expected = (current_app.config.get("CLIENT_TOKEN") or "").strip()
    if token != expected:
        abort(403)

def require_portal_token():
    """
    Allow portal access if ANY of:
      - Authorization: Bearer <PORTAL_TOKEN>
      - ?token=<PORTAL_TOKEN>
      - cookie portal_token=<PORTAL_TOKEN>
    """
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
