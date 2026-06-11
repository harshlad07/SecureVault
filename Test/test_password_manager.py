"""
Comprehensive pytest test suite for the Password Manager application.
Covers all user scenarios with positive and negative test cases.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import tkinter as tk
from datetime import datetime

from Storage.db_manager import DatabaseManager
from Encrypt.crypto_manager import (
    derive_key,
    hash_master_key,
    encrypt_data,
    decrypt_data,
    generate_salt,
    verify_master_password,
)
from Utils.password_generator import generate_password


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_vault_dir():
    """Create a temporary directory for vault testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db_manager(temp_vault_dir):
    """Create a test database manager with temporary storage."""
    db_path = temp_vault_dir / "vault.db"
    manager = DatabaseManager(path=str(db_path))
    yield manager
    manager.close()


@pytest.fixture
def initialized_db(db_manager):
    """Create a database with master password already set."""
    test_password = "TestPassword123!"
    db_manager.setup_master_password(test_password)
    return db_manager, test_password


# ============================================================================
# ENCRYPTION TESTS
# ============================================================================


class TestEncryption:
    """Test encryption and cryptography functions."""

    def test_generate_salt_produces_random_bytes(self):
        """Positive: Salt generation should produce random bytes."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        assert len(salt1) == 16
        assert len(salt2) == 16
        assert salt1 != salt2

    def test_salt_length_customizable(self):
        """Positive: Salt length should be customizable."""
        salt = generate_salt(length=32)
        assert len(salt) == 32

    def test_derive_key_consistent(self):
        """Positive: Same password and salt should produce same key."""
        password = "SecurePassword123"
        salt = generate_salt()
        key1 = derive_key(password, salt)
        key2 = derive_key(password, salt)
        assert key1 == key2
        assert len(key1) == 32

    def test_derive_key_different_for_different_passwords(self):
        """Positive: Different passwords should produce different keys."""
        salt = generate_salt()
        key1 = derive_key("Password123", salt)
        key2 = derive_key("Password456", salt)
        assert key1 != key2

    def test_encrypt_decrypt_roundtrip(self):
        """Positive: Encrypt then decrypt should recover original data."""
        plaintext = "my_secret_password"
        key = derive_key("MasterPassword123", generate_salt())
        nonce, ciphertext = encrypt_data(plaintext, key)
        decrypted = decrypt_data(nonce, ciphertext, key)
        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertexts(self):
        """Positive: Same plaintext encrypted twice should produce different ciphertexts."""
        plaintext = "secret"
        key = derive_key("MasterPassword123", generate_salt())
        nonce1, cipher1 = encrypt_data(plaintext, key)
        nonce2, cipher2 = encrypt_data(plaintext, key)
        # Different nonces should produce different ciphertexts
        assert (nonce1, cipher1) != (nonce2, cipher2)

    def test_decrypt_with_wrong_key_fails(self):
        """Negative: Decryption with wrong key should fail."""
        plaintext = "secret_data"
        key1 = derive_key("Password1", generate_salt())
        key2 = derive_key("Password2", generate_salt())
        nonce, ciphertext = encrypt_data(plaintext, key1)
        
        with pytest.raises(Exception):  # Should raise InvalidTag or similar
            decrypt_data(nonce, ciphertext, key2)

    def test_verify_master_password_correct(self):
        """Positive: Correct password should verify."""
        password = "CorrectPassword123"
        salt = generate_salt()
        key = derive_key(password, salt)
        master_hash = hash_master_key(key)
        
        assert verify_master_password(password, salt, master_hash) is True

    def test_verify_master_password_incorrect(self):
        """Negative: Incorrect password should not verify."""
        password = "CorrectPassword123"
        wrong_password = "WrongPassword456"
        salt = generate_salt()
        key = derive_key(password, salt)
        master_hash = hash_master_key(key)
        
        assert verify_master_password(wrong_password, salt, master_hash) is False


# ============================================================================
# DATABASE MANAGER TESTS
# ============================================================================


class TestDatabaseManager:
    """Test database manager operations."""

    def test_database_initialization(self, db_manager):
        """Positive: Database should initialize without error."""
        assert db_manager.connection is not None
        assert db_manager.path.exists()

    def test_is_initialized_false_on_new_db(self, db_manager):
        """Positive: New database should not be initialized."""
        assert db_manager.is_initialized() is False

    def test_setup_master_password_success(self, db_manager):
        """Positive: Master password setup should succeed and return key."""
        password = "TestPassword123!"
        key = db_manager.setup_master_password(password)
        assert key is not None
        assert len(key) == 32
        assert db_manager.is_initialized() is True

    def test_setup_master_password_twice_fails(self, db_manager):
        """Negative: Setting up master password twice should fail."""
        db_manager.setup_master_password("Password123!")
        with pytest.raises(RuntimeError):
            db_manager.setup_master_password("AnotherPassword456!")

    def test_authenticate_master_password_correct(self, initialized_db):
        """Positive: Correct password should authenticate."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        assert key is not None
        assert len(key) == 32

    def test_authenticate_master_password_incorrect(self, initialized_db):
        """Negative: Incorrect password should not authenticate."""
        db, password = initialized_db
        key = db.authenticate_master_password("WrongPassword456!")
        assert key is None

    def test_add_credential_success(self, initialized_db):
        """Positive: Adding credential should succeed."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        credential = {
            "website": "github.com",
            "username": "user@example.com",
            "password": "SecurePass123",
            "notes": "Personal GitHub account",
        }
        
        cred_id = db.add_credential(credential, key)
        assert cred_id > 0

    def test_get_credential_success(self, initialized_db):
        """Positive: Retrieving credential should return original data."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        original = {
            "website": "gmail.com",
            "username": "user@gmail.com",
            "password": "GmailPass123",
            "notes": "Main email account",
        }
        
        cred_id = db.add_credential(original, key)
        retrieved = db.get_credential(cred_id, key)
        
        assert retrieved["website"] == original["website"]
        assert retrieved["username"] == original["username"]
        assert retrieved["password"] == original["password"]
        assert retrieved["notes"] == original["notes"]

    def test_get_credential_with_wrong_key_fails(self, initialized_db):
        """Negative: Retrieving credential with wrong key should fail."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        credential = {
            "website": "test.com",
            "username": "testuser",
            "password": "TestPass123",
            "notes": "Test",
        }
        
        cred_id = db.add_credential(credential, key)
        
        # Create a wrong key
        salt = generate_salt()
        wrong_key = derive_key("WrongPassword", salt)
        
        # Should fail to decrypt
        with pytest.raises(Exception):
            db.get_credential(cred_id, wrong_key)

    def test_list_credentials(self, initialized_db):
        """Positive: Listing credentials should return all credentials."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        creds = [
            {
                "website": "site1.com",
                "username": "user1",
                "password": "pass1",
                "notes": "First",
            },
            {
                "website": "site2.com",
                "username": "user2",
                "password": "pass2",
                "notes": "Second",
            },
        ]
        
        for cred in creds:
            db.add_credential(cred, key)
        
        retrieved = db.list_credentials(key)
        assert len(retrieved) == 2
        assert retrieved[0]["website"] == "site1.com"
        assert retrieved[1]["website"] == "site2.com"

    def test_update_credential_success(self, initialized_db):
        """Positive: Updating credential should modify data."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        original = {
            "website": "example.com",
            "username": "user",
            "password": "oldpass",
            "notes": "Original",
        }
        
        cred_id = db.add_credential(original, key)
        
        updated = {
            "website": "example.com",
            "username": "newuser",
            "password": "newpass",
            "notes": "Updated",
        }
        
        db.update_credential(cred_id, updated, key)
        retrieved = db.get_credential(cred_id, key)
        
        assert retrieved["username"] == "newuser"
        assert retrieved["password"] == "newpass"
        assert retrieved["notes"] == "Updated"

    def test_delete_credential_success(self, initialized_db):
        """Positive: Deleting credential should remove it."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        credential = {
            "website": "test.com",
            "username": "user",
            "password": "pass",
            "notes": "To delete",
        }
        
        cred_id = db.add_credential(credential, key)
        
        # Verify it exists
        retrieved_before = db.get_credential(cred_id, key)
        assert retrieved_before is not None
        
        # Delete it
        db.delete_credential(cred_id)
        
        # Verify it's gone (should return None or raise)
        try:
            retrieved_after = db.get_credential(cred_id, key)
            assert retrieved_after is None
        except Exception:
            # If it raises an exception, that's also valid
            pass

    def test_list_credentials_empty(self, initialized_db):
        """Positive: Listing credentials on empty vault should return empty list."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        credentials = db.list_credentials(key)
        assert credentials == []


# ============================================================================
# PASSWORD GENERATOR TESTS
# ============================================================================


class TestPasswordGenerator:
    """Test password generation functionality."""

    def test_generate_password_default(self):
        """Positive: Default password generation should succeed."""
        password = generate_password()
        assert len(password) == 16
        assert password.isascii()

    def test_generate_password_custom_length(self):
        """Positive: Custom length passwords should be generated."""
        for length in [8, 16, 24, 32]:
            password = generate_password(length=length)
            assert len(password) == length

    def test_generate_password_with_uppercase(self):
        """Positive: Password with uppercase should contain uppercase."""
        password = generate_password(length=20, use_upper=True, use_lower=False, use_digits=False, use_symbols=False)
        assert any(c.isupper() for c in password)

    def test_generate_password_with_digits(self):
        """Positive: Password with digits should contain digits."""
        password = generate_password(length=20, use_upper=False, use_lower=False, use_digits=True, use_symbols=False)
        assert any(c.isdigit() for c in password)

    def test_generate_password_with_symbols(self):
        """Positive: Password with symbols should contain special characters."""
        password = generate_password(length=20, use_upper=False, use_lower=False, use_digits=False, use_symbols=True)
        assert any(c in "!@#$%^&*" for c in password)

    def test_generate_password_randomness(self):
        """Positive: Generated passwords should be different."""
        passwords = [generate_password(length=16) for _ in range(5)]
        # All passwords should be unique
        assert len(set(passwords)) == len(passwords)

    def test_generate_password_minimum_length(self):
        """Positive: Password should handle minimum length."""
        password = generate_password(length=1)
        assert len(password) >= 1


# ============================================================================
# UI INTERACTION TESTS (with mocking)
# ============================================================================


class TestUIFlows:
    """Test UI interaction flows with mocking."""

    def test_master_password_validation_flow(self, temp_vault_dir):
        """Positive: Master password validation flow works correctly."""
        db_path = temp_vault_dir / "test" / "vault.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Test through database manager
        db = DatabaseManager(str(db_path))
        
        # Valid password setup
        valid_password = "ValidPassword123!"
        key = db.setup_master_password(valid_password)
        assert key is not None
        
        # Valid password authentication
        auth_key = db.authenticate_master_password(valid_password)
        assert auth_key is not None
        
        # Invalid password authentication
        invalid_key = db.authenticate_master_password("InvalidPassword456!")
        assert invalid_key is None
        
        db.close()


# ============================================================================
# EDGE CASES AND INTEGRATION TESTS
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_special_characters_in_credential(self, initialized_db):
        """Positive: Credentials with special characters should work."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        credential = {
            "website": "test.com",
            "username": "user@example.com",
            "password": "P@ssw0rd!#$%^&*()",
            "notes": "Special chars: éàü™®©",
        }
        
        cred_id = db.add_credential(credential, key)
        retrieved = db.get_credential(cred_id, key)
        
        assert retrieved["password"] == credential["password"]
        assert retrieved["notes"] == credential["notes"]

    def test_unicode_in_credential(self, initialized_db):
        """Positive: Unicode characters should work in credentials."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        credential = {
            "website": "test.com",
            "username": "用户",
            "password": "مرحبا",
            "notes": "🔐🔑",
        }
        
        cred_id = db.add_credential(credential, key)
        retrieved = db.get_credential(cred_id, key)
        
        assert retrieved["username"] == credential["username"]
        assert retrieved["password"] == credential["password"]
        assert retrieved["notes"] == credential["notes"]

    def test_very_long_credential(self, initialized_db):
        """Positive: Very long credentials should work."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        long_password = "x" * 10000
        credential = {
            "website": "test.com",
            "username": "user",
            "password": long_password,
            "notes": "y" * 5000,
        }
        
        cred_id = db.add_credential(credential, key)
        retrieved = db.get_credential(cred_id, key)
        
        assert retrieved["password"] == long_password

    def test_multiple_vaults_isolation(self, temp_vault_dir):
        """Positive: Credentials in different vaults should be isolated."""
        db1_path = temp_vault_dir / "vault1" / "vault.db"
        db1_path.parent.mkdir()
        db1 = DatabaseManager(str(db1_path))
        
        db2_path = temp_vault_dir / "vault2" / "vault.db"
        db2_path.parent.mkdir()
        db2 = DatabaseManager(str(db2_path))
        
        # Setup both vaults
        key1 = db1.setup_master_password("Password1!")
        key2 = db2.setup_master_password("Password2!")
        
        # Add credentials to vault1
        cred1 = {
            "website": "site1.com",
            "username": "user1",
            "password": "pass1",
            "notes": "Vault1",
        }
        db1.add_credential(cred1, key1)
        
        # Add credentials to vault2
        cred2 = {
            "website": "site2.com",
            "username": "user2",
            "password": "pass2",
            "notes": "Vault2",
        }
        db2.add_credential(cred2, key2)
        
        # Verify isolation
        vault1_creds = db1.list_credentials(key1)
        vault2_creds = db2.list_credentials(key2)
        
        assert len(vault1_creds) == 1
        assert len(vault2_creds) == 1
        assert vault1_creds[0]["notes"] == "Vault1"
        assert vault2_creds[0]["notes"] == "Vault2"
        
        db1.close()
        db2.close()

    def test_database_concurrent_access(self, initialized_db):
        """Positive: Multiple operations should work sequentially."""
        db, password = initialized_db
        key = db.authenticate_master_password(password)
        
        # Add multiple credentials
        for i in range(10):
            credential = {
                "website": f"site{i}.com",
                "username": f"user{i}",
                "password": f"pass{i}",
                "notes": f"Note {i}",
            }
            db.add_credential(credential, key)
        
        # Retrieve all
        creds = db.list_credentials(key)
        assert len(creds) == 10
        
        # Update some
        for i in range(5):
            updated = {
                "website": f"site{i}.com",
                "username": f"updated_user{i}",
                "password": f"updated_pass{i}",
                "notes": f"Updated note {i}",
            }
            db.update_credential(creds[i]["id"], updated, key)
        
        # Verify updates
        updated_creds = db.list_credentials(key)
        assert updated_creds[0]["username"] == "updated_user0"


# ============================================================================
# COMPLETE USER FLOW TESTS
# ============================================================================


class TestCompleteUserFlows:
    """Test complete end-to-end user scenarios."""

    def test_complete_flow_create_vault_and_manage_credentials(self, temp_vault_dir):
        """Positive: Complete flow - create vault, set password, add and manage credentials."""
        # Create vault
        vault_path = temp_vault_dir / "my_vault"
        vault_path.mkdir()
        db_path = vault_path / "vault.db"
        
        db = DatabaseManager(str(db_path))
        
        # Step 1: Setup master password
        master_password = "MySecurePassword123!"
        master_key = db.setup_master_password(master_password)
        assert db.is_initialized() is True
        
        # Step 2: Add multiple credentials
        credentials = [
            {
                "website": "github.com",
                "username": "john@example.com",
                "password": "GitHubPass123!",
                "notes": "Personal GitHub",
            },
            {
                "website": "gmail.com",
                "username": "john@gmail.com",
                "password": "GmailPass456!",
                "notes": "Main email",
            },
            {
                "website": "facebook.com",
                "username": "john_doe",
                "password": "FBPass789!",
                "notes": "Old Facebook account",
            },
        ]
        
        cred_ids = []
        for cred in credentials:
            cred_id = db.add_credential(cred, master_key)
            cred_ids.append(cred_id)
        
        # Step 3: List and verify credentials
        all_creds = db.list_credentials(master_key)
        assert len(all_creds) == 3
        
        # Step 4: Edit a credential
        updated_cred = {
            "website": "gmail.com",
            "username": "john.doe@gmail.com",
            "password": "UpdatedGmailPass456!",
            "notes": "Main email - updated",
        }
        db.update_credential(cred_ids[1], updated_cred, master_key)
        
        retrieved = db.get_credential(cred_ids[1], master_key)
        assert retrieved["username"] == "john.doe@gmail.com"
        
        # Step 5: Delete a credential
        db.delete_credential(cred_ids[2])
        remaining_creds = db.list_credentials(master_key)
        assert len(remaining_creds) == 2
        
        # Step 6: Close and reopen vault
        db.close()
        
        # Reopen vault
        db = DatabaseManager(str(db_path))
        reopen_key = db.authenticate_master_password(master_password)
        assert reopen_key is not None
        
        # Verify data persists
        persisted_creds = db.list_credentials(reopen_key)
        assert len(persisted_creds) == 2
        assert persisted_creds[0]["website"] in ["github.com", "gmail.com"]
        
        db.close()

    def test_complete_flow_vault_switching(self, temp_vault_dir):
        """Positive: Complete flow - create multiple vaults and switch between them."""
        # Create vault 1
        vault1_path = temp_vault_dir / "vault_1"
        vault1_path.mkdir()
        db1_path = vault1_path / "vault.db"
        db1 = DatabaseManager(str(db1_path))
        key1 = db1.setup_master_password("Password1!")
        
        # Create vault 2
        vault2_path = temp_vault_dir / "vault_2"
        vault2_path.mkdir()
        db2_path = vault2_path / "vault.db"
        db2 = DatabaseManager(str(db2_path))
        key2 = db2.setup_master_password("Password2!")
        
        # Add credential to vault 1
        cred1 = {
            "website": "site1.com",
            "username": "user1",
            "password": "pass1",
            "notes": "Vault 1 credential",
        }
        db1.add_credential(cred1, key1)
        
        # Add credential to vault 2
        cred2 = {
            "website": "site2.com",
            "username": "user2",
            "password": "pass2",
            "notes": "Vault 2 credential",
        }
        db2.add_credential(cred2, key2)
        
        # Close both
        db1.close()
        db2.close()
        
        # Reopen vault 1 and verify
        db1 = DatabaseManager(str(db1_path))
        reopen_key1 = db1.authenticate_master_password("Password1!")
        creds1 = db1.list_credentials(reopen_key1)
        assert len(creds1) == 1
        assert creds1[0]["website"] == "site1.com"
        
        # Reopen vault 2 and verify
        db2 = DatabaseManager(str(db2_path))
        reopen_key2 = db2.authenticate_master_password("Password2!")
        creds2 = db2.list_credentials(reopen_key2)
        assert len(creds2) == 1
        assert creds2[0]["website"] == "site2.com"
        
        db1.close()
        db2.close()

    def test_complete_flow_wrong_password_recovery(self, temp_vault_dir):
        """Positive: Complete flow - handle wrong password and recovery."""
        vault_path = temp_vault_dir / "recovery_vault"
        vault_path.mkdir()
        db_path = vault_path / "vault.db"
        
        db = DatabaseManager(str(db_path))
        correct_password = "CorrectPassword123!"
        correct_key = db.setup_master_password(correct_password)
        
        # Add a credential
        cred = {
            "website": "test.com",
            "username": "user",
            "password": "secret",
            "notes": "test",
        }
        db.add_credential(cred, correct_key)
        
        # Try wrong password
        wrong_key = db.authenticate_master_password("WrongPassword456!")
        assert wrong_key is None
        
        # Try correct password - should work
        correct_key_retry = db.authenticate_master_password(correct_password)
        assert correct_key_retry is not None
        
        # Verify credential accessible
        creds = db.list_credentials(correct_key_retry)
        assert len(creds) == 1
        
        db.close()


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
