from flask import Blueprint, render_template
from ..models.forms import list_active_forms

bp = Blueprint("home", __name__)

@bp.get("/")
def home():
    items = list_active_forms()
    grouped = {}
    for f in items:
        grouped.setdefault(f["client_slug"], []).append(f)
    return render_template("home.html", groups=grouped)
