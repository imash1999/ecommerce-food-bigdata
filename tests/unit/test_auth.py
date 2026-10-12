import pytest

from backend.main import hash_password, verify_password


class TestHashPassword:
    def test_hash_returns_string(self):
        result = hash_password("secret123")
        assert isinstance(result, str)

    def test_hash_format(self):
        result = hash_password("secret123")
        parts = result.split("$")
        assert len(parts) == 4
        assert parts[0] == "pbkdf2_sha256"
        assert parts[1] == "310000"
        assert len(parts[2]) == 32   
        assert len(parts[3]) == 64 

    def test_hash_unique_salt(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2


class TestVerifyPassword:
    def test_verify_correct_password(self):
        password = "my_secret_123"
        stored = hash_password(password)
        assert verify_password(password, stored) is True

    def test_verify_wrong_password(self):
        stored = hash_password("correct_password")
        assert verify_password("wrong_password", stored) is False

    def test_verify_empty_password(self):
        stored = hash_password("some_password")
        assert verify_password("", stored) is False

    def test_verify_invalid_hash_format(self):
        assert verify_password("password", "not_a_valid_hash") is False

    def test_verify_unknown_algorithm(self):
        fake_hash = "md5$1000$abc$def"
        assert verify_password("password", fake_hash) is False

    def test_verify_unicode_password(self):
        password = "пароль123中文"
        stored = hash_password(password)
        assert verify_password(password, stored) is True