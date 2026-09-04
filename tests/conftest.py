import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).resolve().parent / "_pytest.db"
os.environ["MARKET_DATA_PROVIDER"] = "mock"
os.environ["INFORMATION_PROVIDER"] = "mock"
os.environ["AI_PROVIDER"] = "mock"
os.environ["SECRET_KEY"] = "test-secret-key-must-be-32-bytes-min"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

from app.config import get_settings

get_settings.cache_clear()

from app.db import Base, get_db, reset_engine
from app import models  # noqa: F401
from app.main import create_app

reset_engine(os.environ["DATABASE_URL"])

app = create_app()
app.dependency_overrides[get_db] = get_db


@pytest.fixture(autouse=True)
def _clean_db():
    from app.db import engine as test_engine

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def client(_clean_db):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db(_clean_db):
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def auth_header(client: TestClient, email: str, password: str = "password123") -> dict:
    resp = client.post("/api/auth/register", json={"email": email, "password": password})
    if resp.status_code == 409:
        resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
