import os
import time
import json
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
db = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

print("🛡️ AegisVault Dead-Man's Switch Watchdog Container Started...")

while True:
    try:
        for key in db.scan_iter("vault:*"):
            raw = db.get(key)
            if not raw:
                continue
            record = json.loads(raw)
            if record.get("status") == "ACTIVE" and time.time() > record.get("deadline", 0):
                record["status"] = "EXPIRED"
                db.set(key, json.dumps(record))
                print(f"🚨 [SWITCH TRIGGERED] {key} deadline passed! Status updated to EXPIRED.")
    except Exception as e:
        print(f"Waiting for Redis connection... ({e})")
    time.sleep(2)