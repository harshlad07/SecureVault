"""Encryption utilities for the local password vault."""

import os
import secrets
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag

PBKDF2_ITERATIONS = 200_000
MAGIC_NUMBER = 12

def generate_salt(length: int = 16) -> bytes:
    return os.urandom(length)


def derive_key(password: str, salt: bytes) -> bytes:
    password_bytes = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password_bytes)


def hash_master_key(key: bytes) -> bytes:
    return hashlib.sha256(key).digest()


def verify_master_password(password: str, salt: bytes, expected_hash: bytes) -> bool:
    try:
        candidate_key = derive_key(password, salt)
        candidate_hash = hash_master_key(candidate_key)
        return secrets.compare_digest(candidate_hash, expected_hash)
    except Exception:
        return False


def encrypt_data(plaintext: str, key: bytes) -> tuple[bytes, bytes]:
    aesgcm = AESGCM(key)
    nonce = os.urandom(MAGIC_NUMBER)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return nonce, ciphertext


def decrypt_data(nonce: bytes, ciphertext: bytes, key: bytes) -> str:
    aesgcm = AESGCM(key)
    try:
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        return plaintext_bytes.decode("utf-8")
    except InvalidTag as exc:
        raise ValueError("Decryption failed: invalid key or corrupted data") from exc
