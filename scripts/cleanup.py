import os, argparse
from datetime import datetime
from pymongo import MongoClient

def parse_date(s):
    if not s: return None
    return datetime.strptime(s, "%Y-%m-%d")

def end_of_day(dt):
    return dt.replace(hour=23, minute=59, second=59, microsecond=999000)

def build_query(args):
    q = {}
    if args.client:
        q["client_slug"] = args.client
    if args.form:
        q["form_slug"] = args.form
    if args.status:
        q["delivery.status"] = args.status
    if args.date_from or args.date_to:
        rng = {}
        if args.date_from:
            rng["$gte"] = parse_date(args.date_from)
        if args.date_to:
            rng["$lte"] = end_of_day(parse_date(args.date_to))
        q["created_at"] = rng
    if args.seed_only:
        # seed markers used by scripts/seed.py
        q.setdefault("$or", []).extend([
            {"payload.data_source": "seed-script"},
            {"ua": "seed/1.0"},
            {"tags": "test"}
        ])
    return q

def summarize(db, q):
    total = db.submissions.count_documents(q)
    by_status = {}
    for s in ["pending", "delivered", "duplicated", "error"]:
        by_status[s] = db.submissions.count_documents({**q, "delivery.status": s})
    return total, by_status

def prune_orphans(db):
    from bson import ObjectId
    sub_ids = set(db.submissions.distinct("_id"))
    del_sub_ids = db.deliveries.distinct("submission_id")
    orphan_ids = [sid for sid in del_sub_ids if sid not in sub_ids]
    if not orphan_ids:
        return 0
    res = db.deliveries.delete_many({"submission_id": {"$in": orphan_ids}})
    return res.deleted_count

def run(uri, dbname, args):
    mongo = MongoClient(uri)
    db = mongo[dbname]

    if args.prune_orphans:
        removed = prune_orphans(db)
        print(f"Pruned {removed} orphan delivery records.")
        mongo.close()
        return

    q = build_query(args)
    total, by_status = summarize(db, q)
    print("Matched submissions:", total, "by status:", by_status)

    ids = list(db.submissions.find(q, {"_id": 1}))
    id_list = [d["_id"] for d in ids]

    if args.dry_run:
        print(f"[DRY-RUN] Would delete {len(id_list)} submissions and their deliveries.")
        mongo.close()
        return

    # Delete deliveries first (by submission_id)
    del_res = db.deliveries.delete_many({"submission_id": {"$in": id_list}})
    sub_res = db.submissions.delete_many({"_id": {"$in": id_list}})

    print(f"Deleted {sub_res.deleted_count} submissions and {del_res.deleted_count} deliveries.")
    mongo.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up submissions/deliveries safely.")
    parser.add_argument("--uri", default=os.getenv("MONGO_URI", "mongodb://mongo:27017"))
    parser.add_argument("--db", default=os.getenv("MONGO_DB", "marketingdb"))
    parser.add_argument("--client", help="client_slug filter (e.g., leadprosper)")
    parser.add_argument("--form", help="form_slug filter (e.g., zrm-roundup)")
    parser.add_argument("--status", choices=["pending","delivered","duplicated","error"], help="filter by status")
    parser.add_argument("--from", dest="date_from", help="YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", help="YYYY-MM-DD")
    parser.add_argument("--seed-only", action="store_true", help="only delete records created by the seeder (safe)")
    parser.add_argument("--dry-run", action="store_true", help="show what would be deleted")
    parser.add_argument("--prune-orphans", action="store_true", help="remove deliveries that reference missing submissions")
    args = parser.parse_args()
    run(args.uri, args.db, args)
