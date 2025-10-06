from flask import g

def get_form(client_slug, form_slug):
    return g.db.forms.find_one({"client_slug": client_slug, "form_slug": form_slug, "status": "active"})

def list_active_forms():
    cur = g.db.forms.find({"status": "active"}, {"client_slug": 1, "form_slug": 1, "name": 1})
    return list(cur)
