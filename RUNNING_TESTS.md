# Running the Password Manager Tests

## Quick Start

### Run All Tests
```bash
.\env\Scripts\python -m pytest test_password_manager.py -v
```

### Run Specific Test Category
```bash
# Encryption tests only
.\env\Scripts\python -m pytest test_password_manager.py::TestEncryption -v

# Database tests only
.\env\Scripts\python -m pytest test_password_manager.py::TestDatabaseManager -v

# Password generator tests only
.\env\Scripts\python -m pytest test_password_manager.py::TestPasswordGenerator -v

# Edge cases only
.\env\Scripts\python -m pytest test_password_manager.py::TestEdgeCases -v

# Complete user flows only
.\env\Scripts\python -m pytest test_password_manager.py::TestCompleteUserFlows -v
```

### Run Specific Test
```bash
.\env\Scripts\python -m pytest test_password_manager.py::TestDatabaseManager::test_add_credential_success -v
```

### Run with Short Output
```bash
.\env\Scripts\python -m pytest test_password_manager.py -v --tb=short
```

### Run with Detailed Output
```bash
.\env\Scripts\python -m pytest test_password_manager.py -v --tb=long
```

### Stop on First Failure
```bash
.\env\Scripts\python -m pytest test_password_manager.py -v -x
```

### Show Print Statements
```bash
.\env\Scripts\python -m pytest test_password_manager.py -v -s
```

---

## Test Statistics

| Category | Tests | Status |
|----------|-------|--------|
| **Encryption** | 9 | ✅ PASS |
| **Database Manager** | 13 | ✅ PASS |
| **Password Generator** | 7 | ✅ PASS |
| **UI Flows** | 1 | ✅ PASS |
| **Edge Cases** | 5 | ✅ PASS |
| **Complete User Flows** | 3 | ✅ PASS |
| **TOTAL** | **38** | **✅ ALL PASS** |

---

## Test Scenarios Covered

### ✅ Positive Test Cases (30+)
- Vault creation and initialization
- Master password setup
- Credential CRUD operations
- Authentication with correct passwords
- Encryption/decryption
- Password generation with various options
- Data persistence and recovery
- Multiple vault isolation
- Special characters and Unicode support
- Large credential handling

### ✅ Negative Test Cases (8+)
- Duplicate master password setup
- Wrong password authentication
- Decryption with wrong key
- Missing credentials
- Invalid inputs
- Data validation

---

## User Flows Tested

### 1️⃣ Create Vault & Manage Credentials
```
Create vault → Set password → Add credentials → Edit credential → Delete credential → Close vault → Reopen vault → Verify data persists
```

### 2️⃣ Vault Switching
```
Create vault 1 (password A, credentials X) → Create vault 2 (password B, credentials Y) → Switch between vaults → Verify isolation
```

### 3️⃣ Wrong Password Recovery
```
Set up vault → Try wrong password (fails) → Try correct password (succeeds) → Access credentials
```

### 4️⃣ Encryption Security
```
Encrypt data → Try to decrypt with wrong key (fails) → Decrypt with correct key (succeeds)
```

---

## Installation

The tests require pytest. Install it with:

```bash
.\env\Scripts\pip install pytest
```

It's already installed in your environment!

---

## Expected Output

```
============================= test session starts ==============================
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0
collected 38 items

test_password_manager.py::TestEncryption::test_generate_salt_produces_random_bytes PASSED [  2%]
test_password_manager.py::TestEncryption::test_salt_length_customizable PASSED [  5%]
...
test_password_manager.py::TestCompleteUserFlows::test_complete_flow_wrong_password_recovery PASSED [100%]

========================== 38 passed in 3.04s ============================
```

---

## Troubleshooting

**Issue**: Tests hang or don't respond
- Solution: Press `Ctrl+C` to interrupt and run again

**Issue**: ModuleNotFoundError
- Solution: Make sure you're running from the PassManager directory with the virtual environment activated

**Issue**: Pytest not found
- Solution: Install pytest: `.\env\Scripts\pip install pytest`

---

## Creating Custom Tests

Add new test cases to `test_password_manager.py`:

```python
def test_my_custom_scenario(self, initialized_db):
    """Description of what this test does."""
    db, password = initialized_db
    key = db.authenticate_master_password(password)
    
    # Your test code here
    assert True  # Add your assertion
```

---

## Test File Structure

```
test_password_manager.py
├── FIXTURES
│   ├── temp_vault_dir
│   ├── db_manager
│   └── initialized_db
├── TestEncryption (9 tests)
├── TestDatabaseManager (13 tests)
├── TestPasswordGenerator (7 tests)
├── TestUIFlows (1 test)
├── TestEdgeCases (5 tests)
└── TestCompleteUserFlows (3 tests)
```

---

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Test File](./test_password_manager.md)
- [Summary Report](./TEST_SUMMARY.md)
