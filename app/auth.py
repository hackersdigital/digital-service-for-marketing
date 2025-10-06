# app/auth.py
from flask import request, abort, current_app

def require_agent_token():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.form.get("_agent_token", "")
    if token != current_app.config.get("AGENT_TOKEN"):
        abort(403)

def require_client_token():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != current_app.config.get("CLIENT_TOKEN"):
        abort(403)
