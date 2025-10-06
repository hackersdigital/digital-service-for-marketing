from flask import Blueprint, render_template, request, g, Response
from datetime import datetime
from math import ceil
import csv, io

from ..auth import require_portal_token

bp = Blueprint("portal", __name__, url_prefix="/portal")

def _filters_from_request():
    client = request.args.get("client") or None
    form = request.args.get("form") or None
    status = request.args.get("status") or None
    q = request.args.get("q") or None
    date_from = request.args.get("from") or None
    date_to = request.args.get("to") or None

    try: page = int(request.args.get("page", 1))
    except ValueError: page = 1
    page = max(1, page)

    try: page_size = int(request.args.get("page_size", 20))
    except ValueError: page_size = 20
    page_size = max(5, min(page_size, 100))

    return client, form, status, q, date_from, date_to, page, page_size

def _dt_end_of_day(d: datetime) -> datetime:
    return d.replace(hour=23, minute=59, second=59, microsecond=999000)

def _build_query(client, form, status, q, date_from, date_to):
    query = {}
    if client: query["client_slug"] = client
    if form: query["form_slug"] = form
    if status: query["delivery.status"] = status
    if date_from or date_to:
        rng = {}
        if date_from:
            try: rng["$gte"] = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError: pass
        if date_to:
            try: rng["$lte"] = _dt_end_of_day(datetime.strptime(date_to, "%Y-%m-%d"))
            except ValueError: pass
        if rng: query["created_at"] = rng
    if q:
        rx = {"$regex": q, "$options": "i"}
        query["$or"] = [
            {"payload.first_name": rx},
            {"payload.last_name": rx},
            {"payload.email": rx},
            {"payload.number1": rx},
            {"payload.external_id": rx},
        ]
    return query

@bp.get("/")
def portal_home():
    require_portal_token()

    client, form, status, q, date_from, date_to, page, page_size = _filters_from_request()
    query = _build_query(client, form, status, q, date_from, date_to)

    total = g.db.submissions.count_documents(query)
    pages = max(1, ceil(total / page_size))
    cursor = (g.db.submissions.find(query)
              .sort("created_at", -1)
              .skip((page - 1) * page_size)
              .limit(page_size))
    submissions = list(cursor)

    # Fetch latest delivery doc per submission to show outbound request
    delivery_map = {}
    if submissions:
        ids = [s["_id"] for s in submissions]
        # sort by newest attempt first, keep the first encountered per submission_id
        for d in g.db.deliveries.find({"submission_id": {"$in": ids}}).sort("attempted_at", -1):
            sid = d.get("submission_id")
            if sid not in delivery_map:
                delivery_map[sid] = d

    clients = sorted(g.db.submissions.distinct("client_slug"))
    forms = (sorted(g.db.submissions.distinct("form_slug", {"client_slug": client}))
             if client else sorted(g.db.submissions.distinct("form_slug")))
    statuses = ["pending", "delivered", "duplicated", "error"]

    return render_template(
        "portal.html",
        submissions=submissions,
        delivery_map=delivery_map,   # <-- NEW
        total=total,
        page=page,
        pages=pages,
        page_size=page_size,
        filters={"client": client, "form": form, "status": status, "q": q, "from": date_from, "to": date_to},
        options={"clients": clients, "forms": forms, "statuses": statuses},
    )

@bp.get("/export.csv")
def portal_export_csv():
    require_portal_token()
    client, form, status, q, date_from, date_to, _page, _page_size = _filters_from_request()
    query = _build_query(client, form, status, q, date_from, date_to)

    cur = g.db.submissions.find(query).sort("created_at", -1)

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["created_at","client","form","status","first_name","last_name","email","phone","lp_value"])
        yield output.getvalue(); output.seek(0); output.truncate(0)
        for s in cur:
            p = s.get("payload") or {}
            d = s.get("delivery") or {}
            last = d.get("last_result") or {}
            writer.writerow([
                s.get("created_at"),
                s.get("client_slug",""),
                s.get("form_slug",""),
                d.get("status",""),
                p.get("first_name",""),
                p.get("last_name",""),
                p.get("email",""),
                p.get("number1",""),
                last.get("value",""),
            ])
            yield output.getvalue(); output.seek(0); output.truncate(0)

    filename = f"submissions_{client or 'all'}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})
