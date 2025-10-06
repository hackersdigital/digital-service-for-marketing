from flask import Blueprint, render_template, g, request
bp = Blueprint("portal", __name__, url_prefix="/portal")

@bp.get("/")
def portal_home():
    client = request.args.get("client")
    q = {"client_slug": client} if client else {}
    docs = list(g.db.submissions.find(q).sort("created_at", -1).limit(50))
    return render_template("result.html", status="Portal", detail={"records": len(docs)})
