from flask import g

def insert_update(doc):
    return g.db.updates.insert_one(doc).inserted_id
