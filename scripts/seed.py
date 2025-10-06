import os, argparse, random, string
from datetime import datetime, timedelta
from pymongo import MongoClient

def rand_phone():
    r = ''.join(random.choice('0123456789') for _ in range(10))
    return f"({r[:3]}) {r[3:6]}-{r[6:]}"

def rand_email(first, last, i):
    domain = random.choice(["example.com", "mail.com", "inbox.test"])
    return f"{first.lower()}.{last.lower()}{i}@{domain}"

def rand_name():
    firsts = ["Ava","Liam","Noah","Mia","Ethan","Isha","Arjun","Sara","Vik","Anya","Tejas","Riya"]
    lasts  = ["Patel","Sharma","Khan","Rao","Singh","Mehta","Iyer","Kapoor","Das","Menon","Ghosh","Bose"]
    return random.choice(firsts), random.choice(lasts)

def lp_result(status_label):
    # Normalize to a "last_result" shape our portal expects
    if status_label == "delivered":
        body = {"status":"ACCEPTED","code":0,"message":"OK","id":"lp_"+idlike(),"lead_id":"L"+idlike(6)}
        return {"http_status":200,"latency_ms":random.randint(80,300),"body":body,"value":"ACCEPTED","normalized_status":"delivered"}
    if status_label == "duplicated":
        body = {"status":"DUPLICATED","code":208,"message":"Duplicate lead"}
        return {"http_status":200,"latency_ms":random.randint(80,300),"body":body,"value":"DUPLICATED","normalized_status":"duplicated"}
    if status_label == "error":
        body = {"status":"ERROR","code":422,"message":"Validation failed"}
        return {"http_status":422,"latency_ms":random.randint(80,300),"body":body,"value":"ERROR","normalized_status":"error"}
    # pending → no result yet
    return None

def idlike(n=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(n))

def seed(uri, dbname, client_slug, form_slug, count, wipe):
    mongo = MongoClient(uri)
    db = mongo[dbname]

    if wipe:
        db.submissions.delete_many({"client_slug": client_slug, "form_slug": form_slug})
        db.deliveries.delete_many({"request.url": {"$exists": True}})

    # Status weights: delivered 60%, duplicated 20%, error 15%, pending 5%
    choices = (["delivered"]*60) + (["duplicated"]*20) + (["error"]*15) + (["pending"]*5)

    for i in range(count):
        first, last = rand_name()
        created_at = datetime.utcnow() - timedelta(minutes=i)
        status_pick = random.choice(choices)

        payload = {
            "Center_Code": "CC-001",
            "data_source": "seed-script",
            "ip_adress": f"10.0.0.{random.randint(1,254)}",
            "first_name": first,
            "last_name": last,
            "number1": rand_phone(),
            "email": rand_email(first, last, i),
            "other_cancer_type": "Other",
            "Diagnosis_Date": "01/2023",
            "date_of_birth": "02/14/1985",
            "plaid_ID": idlike(10),
            # ensure one of the verification fields
            "verification_id": idlike(6) if random.random() < 0.5 else "",
            "verification_id_2": idlike(6) if random.random() < 0.5 else "",
        }

        sub_doc = {
            "client_slug": client_slug,
            "form_slug": form_slug,
            "created_at": created_at,
            "ip": payload["ip_adress"],
            "ua": "seed/1.0",
            "payload": payload,
            "delivery": {"status": "pending", "attempts": 0}
        }
        sub_id = db.submissions.insert_one(sub_doc).inserted_id

        last_result = lp_result(status_pick)
        if last_result:
            db.deliveries.insert_one({
                "submission_id": sub_id,
                "attempted_at": created_at + timedelta(seconds=2),
                "request": {
                    "url": "https://api.leadprosper.io/direct_post",
                    "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                    "body": {"lp_campaign_id":"29544","lp_supplier_id":"90015","lp_key":"ww2h3mkxbdedg"}  # sample
                },
                "response": last_result
            })
            db.submissions.update_one({"_id": sub_id}, {"$set": {
                "delivery.status": last_result["normalized_status"],
                "delivery.attempts": 1,
                "delivery.last_result": last_result
            }})
        # pending stays as inserted

    print(f"Seeded {count} submissions for {client_slug}/{form_slug} into {dbname}")
    mongo.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Mongo with fake submissions/deliveries")
    parser.add_argument("--uri", default=os.getenv("MONGO_URI","mongodb://mongo:27017"))
    parser.add_argument("--db", default=os.getenv("MONGO_DB","marketingdb"))
    parser.add_argument("--client", default="leadprosper")
    parser.add_argument("--form", default="zrm-roundup")
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--wipe", action="store_true")
    args = parser.parse_args()
    seed(args.uri, args.db, args.client, args.form, args.count, args.wipe)
