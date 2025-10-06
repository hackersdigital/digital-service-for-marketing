# scripts/load_config.py
import os, json, argparse
from datetime import datetime
from pymongo import MongoClient, ASCENDING

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

def _connect():
    uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    dbn = os.getenv("MONGO_DB", "marketingdb")
    cli = MongoClient(uri)
    db = cli[dbn]
    # helpful indexes (no-op if already exist)
    db.clients.create_index([("slug", ASCENDING)], unique=True)
    db.forms.create_index([("client_slug", ASCENDING), ("form_slug", ASCENDING)], unique=True)
    return cli, db

def upsert_clients(db, items):
    for it in items:
        if "slug" not in it: raise SystemExit("Client item missing 'slug'")
        it.setdefault("status", "active")
        it["updated_at"] = datetime.utcnow()
        db.clients.update_one({"slug": it["slug"]}, {"$set": it}, upsert=True)

def upsert_forms(db, items):
    for it in items:
        if "client_slug" not in it or "form_slug" not in it:
            raise SystemExit("Form item missing 'client_slug' or 'form_slug'")
        it.setdefault("status", "active")
        it["updated_at"] = datetime.utcnow()
        db.forms.update_one(
            {"client_slug": it["client_slug"], "form_slug": it["form_slug"]},
            {"$set": it},
            upsert=True,
        )

def main():
    ap = argparse.ArgumentParser(description="Load/Upsert clients & forms from JSON")
    ap.add_argument("--clients", nargs="*", help="one or more client JSON files")
    ap.add_argument("--forms", nargs="*", help="one or more form JSON files")
    args = ap.parse_args()

    cli, db = _connect()
    try:
        if args.clients:
            for p in args.clients:
                upsert_clients(db, _load_json(p))
            print(f"Loaded clients from: {', '.join(args.clients)}")
        if args.forms:
            for p in args.forms:
                upsert_forms(db, _load_json(p))
            print(f"Loaded forms from: {', '.join(args.forms)}")
        if not args.clients and not args.forms:
            print("Nothing to do. Pass --clients and/or --forms with JSON paths.")
    finally:
        cli.close()

if __name__ == "__main__":
    main()
