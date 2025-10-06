# app/api/client.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import require_client_token

def register_client_api(app):
    bp = Blueprint("client_api", __name__, url_prefix="/api")

    @bp.post("/clients/<slug>/updates")
    def client_updates(slug):
        require_client_token()
        payload = request.get_json(silent=True) or {}
        g.db.updates.insert_one({"client_slug": slug, "payload": payload})
        return jsonify(ack=True), 202

    app.register_blueprint(bp)

    @app.get("/client-docs/<slug>")
    def client_docs(slug):
        base = current_app.config.get("BASE_URL", "")
        html = (
            f"<h1>Client Webhook Docs – {slug}</h1>"
            "<p>POST /api/clients/&lt;slug&gt;/updates</p>"
            "<pre>curl -X POST "
            "-H 'Authorization: Bearer CK_TOKEN' "
            "-H 'Content-Type: application/json' "
            f"{base}/api/clients/{slug}/updates "
            "-d '{\"status\":\"example\",\"external_id\":\"123\"}'</pre>"
        )
        return html, 200, {"Content-Type": "text/html"}

# from flask import Blueprint, request, current_app, abort, jsonify, g
# from ..auth import require_client_token

# def register_client_api(app):
#     bp = Blueprint("client_api", __name__, url_prefix="/api")

#     @bp.post("/clients/<slug>/updates")
#     def client_updates(slug):
#         require_client_token()
#         payload = request.get_json(silent=True) or {}
#         g.db.updates.insert_one({"client_slug": slug, "payload": payload})
#         return jsonify(ack=True), 202

#     app.register_blueprint(bp)

#     @app.get("/client-docs/<slug>")
#     def client_docs(slug):
#         return (
#             f"<h1>Client Webhook Docs – {slug}</h1>"
#             "<p>POST /api/clients/&lt;slug&gt;/updates</p>"
#             "<pre>curl -X POST "
#             "-H 'Authorization: Bearer CK_TOKEN' "
#             "-H 'Content-Type: application/json' "
#             f"{app.config['BASE_URL']}/api/clients/{slug}/updates "
#             "-d '{\"status\":\"example\",\"external_id\":\"123\"}'</pre>",
#             200,
#             {"Content-Type": "text/html"}
#         )
