# app/__init__.py
import os
from flask import Flask
from .config import load_config
from .db import init_mongo

# Blueprints
from .views.home import bp as home_bp
from .views.forms import bp as forms_bp
from .views.portal import bp as portal_bp
from .api.internal import register_internal_api
from .api.client import register_client_api

def create_app():
    app = Flask(__name__, template_folder="templates")
    load_config(app)
    init_mongo(app)

    # Register blueprints INSIDE the factory
    app.register_blueprint(home_bp)
    app.register_blueprint(forms_bp)
    app.register_blueprint(portal_bp)
    register_internal_api(app)   # adds /api + /docs
    register_client_api(app)     # adds /api/clients/... + /client-docs/<slug>

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app
