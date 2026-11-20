from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.exc import IntegrityError

from core.config import settings
from core.security import create_access_token, get_password_hash, verify_password
from models.user import User


def test_root_and_health_endpoints(client: TestClient):
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert root_resp.json() == {"message": "Welcome to ReelsToRoute AI API!"}

    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json() == {"status": "ok"}


def test_cors_does_not_allow_arbitrary_origins(client: TestClient):
    allowed_resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert allowed_resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert allowed_resp.headers.get("access-control-allow-credentials") == "true"

    disallowed_resp = client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert disallowed_resp.headers.get("access-control-allow-origin") is None


def test_bcrypt_hashing_and_72_byte_limit():
    hashed = get_password_hash("StrongPass123!")
    assert hashed.startswith("$2b$")
    assert verify_password("StrongPass123!", hashed) is True
    assert verify_password("WrongPass123!", hashed) is False
    assert verify_password("x" * 73, hashed) is False


def test_register_normalizes_email_and_rejects_duplicates(client: TestClient, db_session):
    resp1 = client.post(
        "/auth/register",
        json={
            "email": "User.Name@Example.COM",
            "password": "ValidPassword123",
            "full_name": "Alice",
        },
    )
    assert resp1.status_code == 201
    assert resp1.json()["email"] == "user.name@example.com"

    db_user = db_session.query(User).filter(User.email == "user.name@example.com").first()
    assert db_user is not None
    assert db_user.hashed_password.startswith("$2b$")

    resp2 = client.post(
        "/auth/register",
        json={"email": "user.name@example.com", "password": "AnotherPassword123"},
    )
    assert resp2.status_code == 400


def test_register_handles_integrity_error_cleanly(client: TestClient, monkeypatch):
    from crud import user as crud_user

    def raise_integrity_error(*args, **kwargs):
        raise IntegrityError("INSERT INTO users ...", {}, Exception("UNIQUE constraint failed"))

    monkeypatch.setattr(crud_user, "create_user", raise_integrity_error)

    resp = client.post(
        "/auth/register",
        json={"email": "race@example.com", "password": "ValidPassword123"},
    )
    assert resp.status_code == 400


def test_register_password_validation(client: TestClient):
    short_resp = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert short_resp.status_code == 422

    too_long_resp = client.post(
        "/auth/register",
        json={"email": "long@example.com", "password": "a" * 73},
    )
    assert too_long_resp.status_code == 422

    # 37 two-byte UTF-8 characters = 74 bytes (> 72 bytes even though len < 72)
    multibyte_resp = client.post(
        "/auth/register",
        json={"email": "mb@example.com", "password": "ü" * 37},
    )
    assert multibyte_resp.status_code == 422


def test_login_and_jwt_validation_edge_cases(client: TestClient, auth_headers):
    headers = auth_headers(email="jwt@example.com", password="ValidPassword123")

    ok_resp = client.get("/locations/my-locations", headers=headers)
    assert ok_resp.status_code == 200

    # Login with uppercase email succeeds
    login_upper = client.post(
        "/auth/login",
        data={"username": "JWT@EXAMPLE.COM", "password": "ValidPassword123"},
    )
    assert login_upper.status_code == 200
    assert login_upper.json()["token_type"] == "bearer"

    # Bad password -> 401
    bad_login = client.post(
        "/auth/login",
        data={"username": "jwt@example.com", "password": "WrongPassword123"},
    )
    assert bad_login.status_code == 401

    # Unknown user -> 401 and still runs bcrypt verification for timing parity
    unknown_login = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "SomePassword123"},
    )
    assert unknown_login.status_code == 401

    # Non-integer sub in JWT must return 401 (never 500)
    bad_sub_token = create_access_token(data={"sub": "not-an-integer"})
    bad_sub_resp = client.get(
        "/locations/my-locations",
        headers={"Authorization": f"Bearer {bad_sub_token}"},
    )
    assert bad_sub_resp.status_code == 401

    # Wrong token type must return 401
    wrong_type_token = jwt.encode(
        {
            "sub": "1",
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    wrong_type_resp = client.get(
        "/locations/my-locations",
        headers={"Authorization": f"Bearer {wrong_type_token}"},
    )
    assert wrong_type_resp.status_code == 401

    # Expired token must return 401
    expired_token = create_access_token(
        data={"sub": "1"},
        expires_delta=timedelta(minutes=-5),
    )
    expired_resp = client.get(
        "/locations/my-locations",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired_resp.status_code == 401


def test_auth_endpoints_rate_limiting(client: TestClient):
    for i in range(5):
        resp = client.post(
            "/auth/register",
            json={"email": f"user{i}@example.com", "password": "ValidPassword123"},
        )
        assert resp.status_code == 201

    limited_reg = client.post(
        "/auth/register",
        json={"email": "user5@example.com", "password": "ValidPassword123"},
    )
    assert limited_reg.status_code == 429

    for _ in range(10):
        resp = client.post(
            "/auth/login",
            data={"username": "user0@example.com", "password": "WrongPassword123"},
        )
        assert resp.status_code == 401

    limited_login = client.post(
        "/auth/login",
        data={"username": "user0@example.com", "password": "WrongPassword123"},
    )
    assert limited_login.status_code == 429


def test_login_runs_dummy_password_verification_when_user_missing(client: TestClient, monkeypatch):
    from api.endpoints import auth as auth_endpoint
    from core.security import DUMMY_PASSWORD_HASH

    calls: list[tuple[str, str]] = []
    real_verify = auth_endpoint.verify_password

    def spy_verify(plain: str, hashed: str) -> bool:
        calls.append((plain, hashed))
        return real_verify(plain, hashed)

    monkeypatch.setattr(auth_endpoint, "verify_password", spy_verify)

    resp = client.post(
        "/auth/login",
        data={"username": "nonexistent@example.com", "password": "SomePassword123"},
    )
    assert resp.status_code == 401
    assert calls == [("SomePassword123", DUMMY_PASSWORD_HASH)]
