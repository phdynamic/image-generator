import threading
import time

import pytest

from app.main import app
from app.routers import generate as generate_router


def fake_result(params, **extra):
    return {
        "file_path": "fake.png",
        "thumbnail_path": "thumb_fake.png",
        "seed": params["seed"],
        "steps": params["steps"],
        "cfg_scale": params["cfg_scale"],
        "generation_time": 0.1,
        **extra,
    }


def wait_for(client, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("done", "error"):
            return job
        time.sleep(0.02)
    raise AssertionError("job did not finish")


@pytest.fixture
def fake_generate(open_client, monkeypatch):
    calls = []

    def fake(progress_callback=None, **params):
        calls.append(params)
        if progress_callback:
            progress_callback(1, 1)
        return fake_result(params)

    monkeypatch.setattr(app.state.generator, "generate", fake)
    return open_client, calls


def test_generate_returns_immediately_with_a_job(fake_generate):
    client, _ = fake_generate
    r = client.post("/api/generate", data={"prompt": "a lighthouse"})
    assert r.status_code == 202
    assert r.json()["job_id"]


def test_job_completes_and_saves_to_gallery(fake_generate):
    client, calls = fake_generate
    job = wait_for(client, client.post("/api/generate", data={"prompt": "a unique lighthouse"}).json()["job_id"])
    assert job["status"] == "done"
    assert job["image"]["prompt"] == "a unique lighthouse"
    assert job["image"]["id"]
    listed = client.get("/api/images", params={"search": "unique lighthouse"}).json()
    assert listed["total"] == 1
    assert calls[-1]["seed"] != -1, "a random seed should be chosen when none is given"


def test_sizes_are_snapped_and_model_checked(fake_generate):
    client, calls = fake_generate
    wait_for(client, client.post(
        "/api/generate", data={"prompt": "x", "width": 500, "height": 99999}).json()["job_id"])
    assert calls[-1]["width"] == 496
    assert calls[-1]["height"] == 1024


def test_runtime_errors_reach_the_user(open_client, monkeypatch):
    def boom(progress_callback=None, **params):
        raise RuntimeError("a required package is missing")
    monkeypatch.setattr(app.state.generator, "generate", boom)
    job = wait_for(open_client, open_client.post("/api/generate", data={"prompt": "x"}).json()["job_id"])
    assert job["status"] == "error"
    assert "required package" in job["error"]


def test_out_of_memory_gets_a_helpful_message(open_client, monkeypatch):
    def oom(progress_callback=None, **params):
        raise Exception("CUDA out of memory. Tried to allocate 2.00 GiB")
    monkeypatch.setattr(app.state.generator, "generate", oom)
    job = wait_for(open_client, open_client.post("/api/generate", data={"prompt": "x"}).json()["job_id"])
    assert job["status"] == "error"
    assert "ran out of memory" in job["error"]


def test_unknown_job(open_client):
    assert open_client.get("/api/jobs/does-not-exist").status_code == 404


def test_jobs_run_in_order_and_report_queue_position(open_client, monkeypatch):
    order, release = [], threading.Event()

    def slow(progress_callback=None, **params):
        order.append(params["prompt"])
        release.wait(5)
        return fake_result(params)

    monkeypatch.setattr(app.state.generator, "generate", slow)
    ids = [open_client.post("/api/generate", data={"prompt": f"job{i}"}).json()["job_id"] for i in range(3)]
    time.sleep(0.2)
    assert open_client.get(f"/api/jobs/{ids[0]}").json()["status"] == "running"
    assert open_client.get(f"/api/jobs/{ids[1]}").json()["queue_position"] == 0
    assert open_client.get(f"/api/jobs/{ids[2]}").json()["queue_position"] == 1
    release.set()
    for job_id in ids:
        assert wait_for(open_client, job_id)["status"] == "done"
    assert order == ["job0", "job1", "job2"]


def test_queue_has_a_limit(open_client, monkeypatch):
    release = threading.Event()

    def slow(progress_callback=None, **params):
        release.wait(5)
        return fake_result(params)

    monkeypatch.setattr(app.state.generator, "generate", slow)
    monkeypatch.setattr(generate_router, "MAX_QUEUED_JOBS", 2)
    codes = [open_client.post("/api/generate", data={"prompt": "x"}).status_code for _ in range(5)]
    release.set()
    assert 429 in codes
    assert codes[0] == 202


def test_jobs_require_sign_in(locked_client):
    assert locked_client.get("/api/jobs/abc").status_code == 401
    assert locked_client.post("/api/generate", data={"prompt": "x"}).status_code == 401
