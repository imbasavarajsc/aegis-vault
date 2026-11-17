import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.crypto import create_split_vault, unlock_split_vault

client = TestClient(app)

def test_split_key_encryption_and_decryption():
    secret = "SBI NetBanking: Pass@991 | Locker PIN: 4820"
    encrypted, share_a, share_b = create_split_vault(secret)
    assert secret not in encrypted
    assert unlock_split_vault(encrypted, share_a, share_b) == secret

def test_wrong_beneficiary_key_fails():
    secret = "Private Crypto Seed Phrase"
    encrypted, share_a, _ = create_split_vault(secret)
    _, _, wrong_share_b = create_split_vault("dummy")
    with pytest.raises(Exception):
        unlock_split_vault(encrypted, share_a, wrong_share_b)

def test_premature_unlock_is_blocked_and_expired_unlock_succeeds():
    # 1. Create a vault with a 2-second timer
    res = client.post("/vault/create", data={
        "vault_id": "ci-test-vault",
        "owner_email": "owner@nie.ac.in",
        "beneficiary_email": "family@nie.ac.in",
        "secret": "Emergency Bank PIN: 7788",
        "timeout_sec": 2
    })
    assert res.status_code == 200
    share_b = res.json()["beneficiary_key_share_B"]

    # 2. Attempt unlock immediately (Must be BLOCKED with 403)
    early_res = client.post("/vault/ci-test-vault/unlock", data={"share_b": share_b})
    assert early_res.status_code == 403

    # 3. Wait 3 seconds for Dead-Man's Switch to expire, then unlock (Must SUCCEED with 200)
    time.sleep(3)
    late_res = client.post("/vault/ci-test-vault/unlock", data={"share_b": share_b})
    assert late_res.status_code == 200
    assert late_res.json()["decrypted_secrets"] == "Emergency Bank PIN: 7788"