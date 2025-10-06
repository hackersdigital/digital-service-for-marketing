from flask import g

def insert_submission(doc):
    return g.db.submissions.insert_one(doc).inserted_id

def update_submission(_id, update):
    return g.db.submissions.update_one({"_id": _id}, {"$set": update})
