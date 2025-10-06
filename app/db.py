from pymongo import MongoClient
from flask import g, current_app

def init_mongo(app):
    @app.before_request
    def connect_db():
        if "mongo" not in g:
            g.mongo = MongoClient(current_app.config["MONGO_URI"])
            g.db = g.mongo[current_app.config["MONGO_DB"]]

    @app.teardown_appcontext
    def close_db(exc):
        mongo = g.pop("mongo", None)
        if mongo:
            mongo.close()
