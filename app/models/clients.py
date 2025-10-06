from flask import g

def get_client(slug):
    return g.db.clients.find_one({"slug": slug, "status": "active"})
