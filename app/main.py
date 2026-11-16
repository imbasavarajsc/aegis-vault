import os, json, time, redis
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from app.crypto import create_split_vault, unlock_split_vault

app = FastAPI(title="AegisVault - Zero-Knowledge Digital Will")

local_memory_db = {}
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
    USE_REDIS = True
except Exception:
    USE_REDIS = False

def save_vault(vault_id: str, data: dict):
    if USE_REDIS:
        redis_client.set(f"vault:{vault_id}", json.dumps(data))
    else:
        local_memory_db[vault_id] = data

def get_vault(vault_id: str):
    if USE_REDIS:
        raw = redis_client.get(f"vault:{vault_id}")
        return json.loads(raw) if raw else None
    return local_memory_db.get(vault_id)

@app.get("/", response_class=HTMLResponse)
def home():
    if os.path.exists("app/templates/index.html"):
        with open("app/templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h2>AegisVault Backend Running! Go to <a href='/docs'>/docs</a> to test.</h2>"

@app.post("/vault/create")
def create_vault(vault_id: str = Form(...), owner_email: str = Form(...), beneficiary_email: str = Form(...), secret: str = Form(...), timeout_sec: int = Form(30)):
    encrypted_data, share_a, share_b = create_split_vault(secret)
    record = {
        "vault_id": vault_id, "owner_email": owner_email, "beneficiary_email": beneficiary_email,
        "encrypted_data": encrypted_data, "share_a": share_a, "timeout_sec": timeout_sec,
        "deadline": time.time() + timeout_sec, "status": "ACTIVE"
    }
    save_vault(vault_id, record)
    return {"status": "LOCKED", "vault_id": vault_id, "beneficiary_key_share_B": share_b, "expires_in_seconds": timeout_sec}

@app.get("/vault/{vault_id}/status")
def check_status(vault_id: str):
    record = get_vault(vault_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vault ID not found")
    remaining = max(0, int(record["deadline"] - time.time()))
    if remaining == 0 and record["status"] == "ACTIVE":
        record["status"] = "EXPIRED"
        save_vault(vault_id, record)
    return {"vault_id": vault_id, "status": record["status"], "seconds_remaining": remaining}

@app.post("/vault/{vault_id}/checkin")
def owner_checkin(vault_id: str):
    record = get_vault(vault_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vault ID not found")
    record["deadline"] = time.time() + record["timeout_sec"]
    record["status"] = "ACTIVE"
    save_vault(vault_id, record)
    return {"status": "ACTIVE", "message": "Heartbeat confirmed! Timer reset."}

@app.post("/vault/{vault_id}/unlock")
def beneficiary_unlock(vault_id: str, share_b: str = Form(...)):
    record = get_vault(vault_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vault ID not found")
    if time.time() > record["deadline"]:
        record["status"] = "EXPIRED"
        save_vault(vault_id, record)
    if record["status"] != "EXPIRED":
        remaining = max(0, int(record["deadline"] - time.time()))
        raise HTTPException(status_code=403, detail=f"ACCESS DENIED: Owner active. Unlocks in {remaining}s.")
    try:
        plaintext = unlock_split_vault(record["encrypted_data"], record["share_a"], share_b.strip())
        return {"status": "UNLOCKED", "decrypted_secrets": plaintext}
    except Exception:
        raise HTTPException(status_code=401, detail="INVALID KEY SHARE B: Decryption failed.")