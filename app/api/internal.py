from flasgger import Swagger
from flask import Blueprint, jsonify

def register_internal_api(app):
    template = {
        "swagger": "2.0",
        "info": {"title": "Internal Admin API", "version": "1.0"},
        "basePath": "/api"
    }
    Swagger(app, template=template)

    bp = Blueprint("internal", __name__, url_prefix="/api")

    @bp.get("/ping")
    def ping():
        """Ping the API
        ---
        responses:
          200:
            description: OK
        """
        return jsonify(ok=True)

    app.register_blueprint(bp)

    @app.route("/docs")
    def docs_redirect():
        from flask import redirect
        return redirect("/apidocs")
