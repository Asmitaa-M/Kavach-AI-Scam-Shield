import os, tempfile, pathlib
_tmp = pathlib.Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.db import init_db


@pytest.fixture(scope="session")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


_n = {"i": 0}

def make_user(client, name="Asha", email=None):
    _n["i"] += 1
    email = email or f"user{_n['i']}@example.com"
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": "StrongPass123"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, email


@pytest.fixture()
def user(client):
    return make_user(client)[0]
