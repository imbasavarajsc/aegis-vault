import os
import base64
from cryptography.fernet import Fernet

def create_split_vault(secret_text: str):
    master_key = Fernet.generate_key()
    cipher = Fernet(master_key)
    encrypted_data = cipher.encrypt(secret_text.encode()).decode()
    
    raw_key = base64.urlsafe_b64decode(master_key)
    share_b_raw = os.urandom(len(raw_key))
    share_a_raw = bytes(a ^ b for a, b in zip(raw_key, share_b_raw))
    
    share_a = base64.urlsafe_b64encode(share_a_raw).decode()
    share_b = base64.urlsafe_b64encode(share_b_raw).decode()
    return encrypted_data, share_a, share_b

def unlock_split_vault(encrypted_data: str, share_a: str, share_b: str) -> str:
    a_raw = base64.urlsafe_b64decode(share_a)
    b_raw = base64.urlsafe_b64decode(share_b)
    if len(a_raw) != len(b_raw):
        raise ValueError("Invalid key share length")
    reconstructed_raw = bytes(a ^ b for a, b in zip(a_raw, b_raw))
    master_key = base64.urlsafe_b64encode(reconstructed_raw)
    return Fernet(master_key).decrypt(encrypted_data.encode()).decode()