# app/auth.py
import logging
from flask import request, abort, current_app

log = logging.getLogger(__name__)

def _bearer_token_from_header() -> str:
    """Return Bearer token from Authorization header, or '' if not present/unsupported."""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return ""

def _collect_agent_tokens():
    """
    Collect possible tokens from multiple sources.
    Returns: (picked_token:str, present_sources:set[str])
    """
    sources_present = set()

    bearer = _bearer_token_from_header()
    if bearer:
        sources_present.add("bearer")

    form_tok = (request.form.get("_agent_token", "") or "").strip()
    if form_tok:
        sources_present.add("form")

    query_tok = (request.args.get("token", "") or "").strip()
    if query_tok:
        sources_present.add("query")

    cookie_tok = (request.cookies.get("portal_token", "") or "").strip()
    if cookie_tok:
        sources_present.add("cookie")

    x_portal_tok = (request.headers.get("X-Portal-Token", "") or "").strip()
    if x_portal_tok:
        sources_present.add("x-portal-token")

    # precedence: Bearer > X-Portal-Token > form > query > cookie
    picked = bearer or x_portal_tok or form_tok or query_tok or cookie_tok
    return picked, sources_present

def require_agent_token():
    """
    Accept ANY of these as a valid agent auth:
      - Authorization: Bearer <AGENT_TOKEN or PORTAL_TOKEN>
      - X-Portal-Token: <PORTAL_TOKEN>
      - form field _agent_token=<AGENT_TOKEN> (legacy/testing)
      - ?token=<PORTAL_TOKEN>
      - cookie portal_token=<PORTAL_TOKEN> (set by visiting /portal?token=...)
    """
    token, sources_present = _collect_agent_tokens()
    agent_expected  = (current_app.config.get("AGENT_TOKEN") or "").strip()
    portal_expected = (current_app.config.get("PORTAL_TOKEN") or "").strip()

    if token not in {agent_expected, portal_expected}:
        # No secrets logged: only which sources were present and whether env vars exist.
        log.warning(
            "Agent auth failed: sources=%s env(agent)=%s env(portal)=%s",
            sorted(sources_present), bool(agent_expected), bool(portal_expected)
        )
        abort(403)

def require_client_token():
    """Client webhooks must provide Authorization: Bearer <CLIENT_TOKEN>."""
    token = _bearer_token_from_header()
    expected = (current_app.config.get("CLIENT_TOKEN") or "").strip()
    if token != expected:
        abort(403)

def require_portal_token():
    """
    Allow portal access if ANY of:
      - Authorization: Bearer <PORTAL_TOKEN>
      - X-Portal-Token: <PORTAL_TOKEN>
      - ?token=<PORTAL_TOKEN>
      - cookie portal_token=<PORTAL_TOKEN>
    """
    token = (
        _bearer_token_from_header()
        or (request.headers.get("X-Portal-Token", "") or "").strip()
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
