"""Database manager for the local encrypted password vault."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from encrypt.crypto_manager import (
    generate_salt,
    derive_key,
    hash_master_key,
    verify_master_password,
    encrypt_data,
    decrypt_data,
)

DB_FILENAME = "vault.db"


def _get_default_db_path() -> Path:
    """Resolve the local vault file path relative to this module."""
    return Path(__file__).resolve().parent / DB_FILENAME


def _iso_now() -> str:
    """Return the current UTC timestamp as an ISO formatted string."""
    return datetime.utcnow().isoformat(timespec="seconds")


class DatabaseManager:
    """Manage vault storage and encrypted credential records."""

    def __init__(self, path: str | None = None):
        self.path = Path(path) if path is not None else _get_default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create the auth and credentials tables if they do not already exist."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auth (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                salt BLOB NOT NULL,
                master_hash BLOB NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nonce BLOB NOT NULL,
                ciphertext BLOB NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def is_initialized(self) -> bool:
        """Return True when the vault has already been initialized."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM auth")
        count = cursor.fetchone()[0]
        return count > 0

    def setup_master_password(self, password: str) -> bytes:
        """Initialize the master password and create auth metadata.

        This stores a random salt and a hashed derived key in the auth table.
        The derived AES key is returned for immediate use.
        """
        if self.is_initialized():
            raise RuntimeError("Master password has already been initialized.")

        salt = generate_salt()
        key = derive_key(password, salt)
        master_hash = hash_master_key(key)
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO auth (id, salt, master_hash, created_at) VALUES (1, ?, ?, ?)",
            (salt, master_hash, _iso_now()),
        )
        self.connection.commit()
        return key

    def authenticate_master_password(self, password: str) -> bytes | None:
        """Verify the password and return the derived encryption key when valid."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT salt, master_hash FROM auth WHERE id = 1")
        row = cursor.fetchone()
        if row is None:
            return None

        salt = row["salt"]
        master_hash = row["master_hash"]
        if verify_master_password(password, salt, master_hash):
            return derive_key(password, salt)
        return None

    def add_credential(self, credential: dict, key: bytes) -> int:
        """Encrypt and insert a new credential into the vault."""
        payload = json.dumps(credential)
        nonce, ciphertext = encrypt_data(payload, key)
        cursor = self.connection.cursor()
        created_at = _iso_now()
        cursor.execute(
            "INSERT INTO credentials (nonce, ciphertext, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (nonce, ciphertext, created_at, created_at),
        )
        self.connection.commit()
        return cursor.lastrowid

    def list_credentials(self, key: bytes) -> list[dict]:
        """Return all decrypted credential records ordered by most recent update."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, nonce, ciphertext, created_at, updated_at FROM credentials ORDER BY updated_at DESC")
        records = []
        for row in cursor.fetchall():
            plaintext = decrypt_data(row["nonce"], row["ciphertext"], key)
            payload = json.loads(plaintext)
            payload["id"] = row["id"]
            payload["created_at"] = row["created_at"]
            payload["updated_at"] = row["updated_at"]
            records.append(payload)
        return records

    def get_credential(self, record_id: int, key: bytes) -> dict | None:
        """Return a single decrypted credential by its record ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT nonce, ciphertext, created_at, updated_at FROM credentials WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        plaintext = decrypt_data(row["nonce"], row["ciphertext"], key)
        payload = json.loads(plaintext)
        payload["id"] = record_id
        payload["created_at"] = row["created_at"]
        payload["updated_at"] = row["updated_at"]
        return payload

    def update_credential(self, record_id: int, credential: dict, key: bytes) -> None:
        """Encrypt and update an existing credential record."""
        payload = json.dumps(credential)
        nonce, ciphertext = encrypt_data(payload, key)
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE credentials SET nonce = ?, ciphertext = ?, updated_at = ? WHERE id = ?",
            (nonce, ciphertext, _iso_now(), record_id),
        )
        self.connection.commit()

    def delete_credential(self, record_id: int) -> None:
        """Remove a credential from the vault."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM credentials WHERE id = ?", (record_id,))
        self.connection.commit()

    def close(self) -> None:
        """Close the SQLite connection when the app shuts down."""
        self.connection.close()
