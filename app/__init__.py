
import os
from flask import Flask
from .config import load_config
from .db import init_mongo
from .views.home import bp as home_bp
from .views.forms import bp as forms_bp
from .api.internal import register_internal_api
from .api.client import register_client_api

def create_app():
    app = Flask(__name__, template_folder="templates")
    load_config(app)
    init_mongo(app)

    # Blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(forms_bp)
    register_internal_api(app)
    register_client_api(app)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app
