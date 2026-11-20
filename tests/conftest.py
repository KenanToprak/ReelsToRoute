import os
from pathlib import Path

# Set required env vars before importing application modules so tests never need .env
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-suite-minimum-32-chars")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from core.limiter import limiter
from main import app
import models.user  # noqa: F401
import models.location  # noqa: F401


@pytest.fixture()
def db_session(tmp_path: Path):
    db_file = tmp_path / "test_app.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    limiter.reset()


@pytest.fixture()
def auth_headers(client: TestClient):
    def _create_user_and_headers(
        email: str = "traveler@example.com",
        password: str = "StrongPass123!",
        full_name: str = "Test Traveler",
    ) -> dict[str, str]:
        reg_resp = client.post(
            "/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        assert reg_resp.status_code == 201, reg_resp.text
        login_resp = client.post(
            "/auth/login",
            data={"username": email, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _create_user_and_headers
