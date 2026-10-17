import os
import sys
import tempfile
from pathlib import Path

# Point the app at throwaway locations *before* it is imported.
_tmp = tempfile.mkdtemp(prefix="imaginaree-test-")
os.environ.update(
    DATABASE_URL=f"sqlite:///{_tmp}/test.db",
    OUTPUTS_DIR=f"{_tmp}/images",
    THUMBNAILS_DIR=f"{_tmp}/thumbs",
    MODELS_CACHE_DIR=f"{_tmp}/models",
    SESSION_SECRET="test-secret",
    APP_PASSWORD_HASH="",
    PUBLIC_MODE="false",
)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import auth
from app.config import settings
from app.main import app
from app.passwords import hash_password

PASSWORD = "correct horse battery"


@pytest.fixture(autouse=True)
def _reset_limiter():
    auth.login_limiter = auth.LoginLimiter()
    # the router module holds a reference via `auth.`, so rebinding above is enough
    yield


@pytest.fixture
def open_client(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", "")
    with TestClient(app) as client:
        yield client


@pytest.fixture
def locked_client(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", hash_password(PASSWORD))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def signed_in(locked_client):
    r = locked_client.post("/api/auth/login", json={"password": PASSWORD})
    assert r.status_code == 200
    return locked_client
