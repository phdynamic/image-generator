import threading
import time

import pytest

from app.main import app
from app.services import model_cache
from app.services.downloads import download_manager, friendly_error

MODEL = "RunDiffusion/Juggernaut-XL-v9"   # has a known download size
OTHER = "SG161222/RealVisXL_V5.0"
MB = 1024 * 1024


@pytest.fixture(autouse=True)
def clean_state():
    download_manager._states.clear()
    download_manager._active = None
    for m in (MODEL, OTHER):
        model_cache.delete(m)
    yield
    download_manager._states.clear()
    download_manager._active = None
    for m in (MODEL, OTHER):
        model_cache.delete(m)


def write_finished(model_id):
    root = model_cache.repo_dir(model_id)
    (root / "blobs").mkdir(parents=True, exist_ok=True)
    (root / "snapshots" / "abc").mkdir(parents=True, exist_ok=True)
    (root / "blobs" / "h1").write_bytes(b"x" * MB)
    (root / "snapshots" / "abc" / "unet.safetensors").write_bytes(b"x" * MB)


def info(client, model_id):
    return next(m for m in client.get("/api/models").json() if m["id"] == model_id)


def wait_until(predicate, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("condition not met in time")


# -- "is it downloaded?" ------------------------------------------------------

def test_not_cached_by_default(open_client):
    m = info(open_client, MODEL)
    assert m["is_cached"] is False and m["download"] is None


def test_finished_download_counts(open_client):
    write_finished(MODEL)
    assert info(open_client, MODEL)["is_cached"] is True


def test_partial_download_does_not_count(open_client):
    write_finished(MODEL)
    (model_cache.repo_dir(MODEL) / "blobs" / "h2.incomplete").write_bytes(b"x")
    assert info(open_client, MODEL)["is_cached"] is False


def test_empty_cache_folder_does_not_count(open_client):
    (model_cache.repo_dir(MODEL) / "snapshots").mkdir(parents=True)
    assert info(open_client, MODEL)["is_cached"] is False


# -- starting a download ------------------------------------------------------

def test_download_reports_progress_then_finishes(open_client, monkeypatch):
    release = threading.Event()

    def fake_download(spec):
        blobs = model_cache.repo_dir(spec.id) / "blobs"
        blobs.mkdir(parents=True, exist_ok=True)
        (blobs / "h1.incomplete").write_bytes(b"x" * (5 * MB))
        release.wait(5)
        write_finished(spec.id)
        (blobs / "h1.incomplete").unlink()

    monkeypatch.setattr(app.state.model_manager, "download_model", fake_download)
    r = open_client.post("/api/models/download", json={"model_id": MODEL})
    assert r.status_code == 202

    wait_until(lambda: info(open_client, MODEL)["download"]["downloaded_bytes"] >= 5 * MB)
    d = info(open_client, MODEL)["download"]
    assert d["status"] == "downloading" and d["total_bytes"] == 7 * 1024 ** 3
    assert info(open_client, MODEL)["is_cached"] is False

    release.set()
    wait_until(lambda: info(open_client, MODEL)["is_cached"])
    assert info(open_client, MODEL)["download"] is None


def test_only_one_download_at_a_time(open_client, monkeypatch):
    release = threading.Event()
    monkeypatch.setattr(app.state.model_manager, "download_model", lambda spec: release.wait(5))
    assert open_client.post("/api/models/download", json={"model_id": MODEL}).status_code == 202
    r = open_client.post("/api/models/download", json={"model_id": OTHER})
    assert r.status_code == 409 and "Juggernaut" in r.json()["detail"]
    release.set()
    wait_until(lambda: download_manager.active() is None)


def test_failed_download_reports_error_and_can_retry(open_client, monkeypatch):
    def boom(spec):
        raise RuntimeError("network unreachable")

    monkeypatch.setattr(app.state.model_manager, "download_model", boom)
    open_client.post("/api/models/download", json={"model_id": MODEL})
    wait_until(lambda: (info(open_client, MODEL)["download"] or {}).get("status") == "error")
    assert "network unreachable" in info(open_client, MODEL)["download"]["error"]

    monkeypatch.setattr(app.state.model_manager, "download_model", lambda spec: write_finished(spec.id))
    assert open_client.post("/api/models/download", json={"model_id": MODEL}).status_code == 202
    wait_until(lambda: info(open_client, MODEL)["is_cached"])


def test_already_downloaded(open_client):
    write_finished(MODEL)
    assert open_client.post("/api/models/download", json={"model_id": MODEL}).status_code == 409


def test_unknown_model_rejected(open_client):
    assert open_client.post("/api/models/download", json={"model_id": "evil/repo"}).status_code == 400
    assert open_client.post("/api/models/delete", json={"model_id": "evil/repo"}).status_code == 400


def test_refuses_when_disk_is_too_small(open_client, monkeypatch):
    monkeypatch.setattr(model_cache, "free_disk_bytes", lambda: 1024 ** 3)
    r = open_client.post("/api/models/download", json={"model_id": MODEL})
    assert r.status_code == 507 and "disk space" in r.json()["detail"]


def test_friendly_errors(monkeypatch):
    class GatedRepoError(Exception):
        pass
    monkeypatch.setattr("app.services.downloads.hf_token_available", lambda: False)
    no_token = friendly_error(GatedRepoError("401 Client Error"), "org/model")
    assert "HF_TOKEN" in no_token and "huggingface.co/org/model" in no_token
    monkeypatch.setattr("app.services.downloads.hf_token_available", lambda: True)
    with_token = friendly_error(GatedRepoError("401 Client Error"), "org/model")
    assert "same account" in with_token and "HF_TOKEN" not in with_token
    assert "disk is full" in friendly_error(OSError(28, "No space left on device"))
    assert friendly_error(RuntimeError("plain")) == "plain"


# -- deleting -----------------------------------------------------------------

def test_delete_frees_the_model(open_client):
    write_finished(MODEL)
    assert open_client.post("/api/models/delete", json={"model_id": MODEL}).status_code == 200
    assert info(open_client, MODEL)["is_cached"] is False
    assert not model_cache.repo_dir(MODEL).exists()


def test_cannot_delete_while_downloading(open_client, monkeypatch):
    release = threading.Event()
    monkeypatch.setattr(app.state.model_manager, "download_model", lambda spec: release.wait(5))
    open_client.post("/api/models/download", json={"model_id": MODEL})
    assert open_client.post("/api/models/delete", json={"model_id": MODEL}).status_code == 409
    release.set()
    wait_until(lambda: download_manager.active() is None)


def test_cannot_delete_during_generation(open_client):
    write_finished(MODEL)
    with app.state.generator.lock:
        assert open_client.post("/api/models/delete", json={"model_id": MODEL}).status_code == 409
    assert model_cache.repo_dir(MODEL).exists()


def test_delete_unloads_a_loaded_model(open_client):
    write_finished(MODEL)
    app.state.model_manager.current_model_id = MODEL
    app.state.model_manager.pipeline = object()
    open_client.post("/api/models/delete", json={"model_id": MODEL})
    assert app.state.model_manager.current_model_id is None


# -- sign-in ------------------------------------------------------------------

def test_download_endpoints_need_sign_in(locked_client):
    assert locked_client.post("/api/models/download", json={"model_id": MODEL}).status_code == 401
    assert locked_client.post("/api/models/delete", json={"model_id": MODEL}).status_code == 401


# -- gated models (FLUX) --------------------------------------------------------

FLUX = "black-forest-labs/FLUX.1-schnell"


def test_gated_model_without_token_fails_fast(open_client, monkeypatch):
    monkeypatch.setattr("app.routers.models_router.hf_token_available", lambda: False)
    m = info(open_client, FLUX)
    assert m["gated"] is True and m["needs_token"] is True
    r = open_client.post("/api/models/download", json={"model_id": FLUX})
    assert r.status_code == 400
    assert "HF_TOKEN" in r.json()["detail"] and "huggingface.co/black-forest-labs/FLUX.1-schnell" in r.json()["detail"]
    assert download_manager.active() is None, "nothing should have started"


def test_gated_model_with_token_can_download(open_client, monkeypatch):
    monkeypatch.setattr("app.routers.models_router.hf_token_available", lambda: True)
    monkeypatch.setattr(model_cache, "free_disk_bytes", lambda: 10 ** 13)
    monkeypatch.setattr(app.state.model_manager, "download_model", lambda spec: write_finished(spec.id))
    assert info(open_client, FLUX)["needs_token"] is False
    assert open_client.post("/api/models/download", json={"model_id": FLUX}).status_code == 202
    wait_until(lambda: info(open_client, FLUX)["is_cached"])
    model_cache.delete(FLUX)


def test_ungated_models_never_need_a_token(open_client, monkeypatch):
    monkeypatch.setattr("app.routers.models_router.hf_token_available", lambda: False)
    assert info(open_client, MODEL)["needs_token"] is False
