"""
Auth katmanı testleri (Faz 9).

Kapsam:
  - JWT oluşturma / çözme / süre aşımı
  - Şifre doğrulama (bcrypt)
  - authenticate_user başarılı + başarısız yollar
  - POST /api/auth/login uçtan uca (TestClient)
  - Korumalı endpoint'ler: token yok / geçersiz / geçerli
  - Öğretmen yetkisi koruması (require_teacher)
  - Username path traversal koruması (storage._validate_username)
"""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Bütün auth importları SECRET_KEY gerektirir
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use")

from backend.auth import (
    ALGORITHM,
    SECRET_KEY,
    TOKEN_EXPIRE_HOURS,
    authenticate_user,
    create_access_token,
    get_current_user,
    verify_password,
)
from backend.main import app
from modules.storage import _validate_username


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def student_token():
    return create_access_token({"sub": "ali", "name": "Ali", "role": "student"})


@pytest.fixture
def teacher_token():
    return create_access_token({"sub": "ogretmen", "name": "Öğr", "role": "teacher"})


# ── Şifre Doğrulama ────────────────────────────────────────────────────────

class TestPasswordVerification:
    def test_verify_correct_password(self):
        import bcrypt
        hashed = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
        assert verify_password("secret123", hashed) is True

    def test_verify_wrong_password(self):
        import bcrypt
        hashed = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
        assert verify_password("wrong", hashed) is False

    def test_verify_malformed_hash_returns_false(self):
        assert verify_password("anything", "not-a-valid-bcrypt-hash") is False


# ── authenticate_user ──────────────────────────────────────────────────────

class TestAuthenticateUser:
    def test_valid_student(self):
        user = authenticate_user("ali", "ali123")
        assert user is not None
        assert user["username"] == "ali"
        assert user["role"] == "student"

    def test_valid_teacher(self):
        user = authenticate_user("ogretmen", "ogr123")
        assert user is not None
        assert user["role"] == "teacher"

    def test_wrong_password_returns_none(self):
        assert authenticate_user("ali", "wrong-password") is None

    def test_unknown_user_returns_none(self):
        assert authenticate_user("nonexistent-user", "any") is None


# ── JWT Token ──────────────────────────────────────────────────────────────

class TestJWT:
    def test_create_and_decode_roundtrip(self):
        token = create_access_token({"sub": "ali", "role": "student"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "ali"
        assert payload["role"] == "student"
        assert "exp" in payload

    def test_token_has_expiry_within_window(self):
        token = create_access_token({"sub": "ali"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = exp - now
        # Süre yaklaşık TOKEN_EXPIRE_HOURS olmalı (saniye toleransı)
        assert timedelta(hours=TOKEN_EXPIRE_HOURS - 1) < delta <= timedelta(hours=TOKEN_EXPIRE_HOURS)

    def test_get_current_user_with_valid_token(self, student_token):
        user = get_current_user(token=student_token)
        assert user["username"] == "ali"
        assert user["role"] == "student"

    def test_get_current_user_rejects_invalid_token(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="not.a.real.jwt")
        assert exc.value.status_code == 401

    def test_get_current_user_rejects_expired_token(self):
        from fastapi import HTTPException
        # Geçmiş tarihli token üret
        payload = {"sub": "ali", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
        expired = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=expired)
        assert exc.value.status_code == 401

    def test_get_current_user_rejects_wrong_signature(self):
        from fastapi import HTTPException
        # Farklı secret ile imzala
        payload = {"sub": "ali", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        bad = jwt.encode(payload, "some-other-secret", algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=bad)
        assert exc.value.status_code == 401

    def test_get_current_user_rejects_token_without_sub(self):
        from fastapi import HTTPException
        payload = {"role": "student", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=token)
        assert exc.value.status_code == 401


# ── /api/auth/login ────────────────────────────────────────────────────────

class TestLoginEndpoint:
    def test_login_success(self, client):
        r = client.post("/api/auth/login", data={"username": "ali", "password": "ali123"})
        assert r.status_code == 200
        body = r.json()
        assert body["username"] == "ali"
        assert body["role"] == "student"
        assert body["access_token"]
        assert body["token_type"].lower() == "bearer"

    def test_login_wrong_password(self, client):
        r = client.post("/api/auth/login", data={"username": "ali", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/api/auth/login", data={"username": "ghost", "password": "x"})
        assert r.status_code == 401

    def test_login_missing_fields(self, client):
        r = client.post("/api/auth/login", data={"username": "ali"})
        assert r.status_code in (400, 422)


# ── Korumalı endpoint erişim kontrolü ──────────────────────────────────────

class TestProtectedEndpoints:
    def test_mastery_requires_auth(self, client):
        r = client.get("/api/mastery/me")
        assert r.status_code == 401

    def test_mastery_rejects_invalid_token(self, client):
        r = client.get("/api/mastery/me", headers={"Authorization": "Bearer bogus.token.here"})
        assert r.status_code == 401

    def test_mastery_accepts_valid_token(self, client, student_token):
        r = client.get("/api/mastery/me", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 200

    def test_teacher_endpoint_rejects_student(self, client, student_token):
        r = client.get("/api/teacher/students", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 403

    def test_teacher_endpoint_accepts_teacher(self, client, teacher_token):
        r = client.get("/api/teacher/students", headers={"Authorization": f"Bearer {teacher_token}"})
        assert r.status_code == 200


# ── Username path traversal koruması ───────────────────────────────────────

class TestUsernameValidation:
    @pytest.mark.parametrize("name", ["ali", "ayse", "ogretmen", "user_01", "test-user"])
    def test_valid_usernames(self, name):
        assert _validate_username(name) == name

    @pytest.mark.parametrize("name", [
        "../etc/passwd",
        "..",
        "a/b",
        "a\\b",
        "ab",        # 3 karakterden kısa
        "a" * 33,    # 32 karakterden uzun
        "",
        "user name", # boşluk
        "user.name", # nokta
        None,
        123,
    ])
    def test_invalid_usernames_raise(self, name):
        with pytest.raises(ValueError):
            _validate_username(name)
