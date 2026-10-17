import pytest

from app.services.model_registry import MODELS, get_spec
from tests.conftest import PASSWORD  # noqa: F401  (ensures env is set up first)


def test_registry_ids_unique():
    ids = [m.id for m in MODELS]
    assert len(ids) == len(set(ids))


def test_default_model_is_first_and_registered():
    from app.config import settings
    assert MODELS[0].id == settings.DEFAULT_MODEL
    assert get_spec(settings.DEFAULT_MODEL)


def test_defaults_are_within_limits():
    for m in MODELS:
        assert 1 <= m.default_steps <= m.max_steps, m.id
        assert m.default_size % 16 == 0, m.id


def test_models_endpoint_exposes_defaults(open_client):
    data = open_client.get("/api/models").json()
    assert len(data) == len(MODELS)
    turbo = next(m for m in data if m["id"] == "stabilityai/sdxl-turbo")
    assert turbo["fixed_cfg"] == 0.0 and turbo["supports_negative"] is False
    assert {"default_steps", "default_cfg", "default_size", "is_cached", "is_loaded",
            "experimental", "type", "vram"} <= set(turbo)


def test_unknown_model_is_rejected(open_client):
    r = open_client.post("/api/generate", data={"prompt": "a cat", "model_id": "evil/pickle-repo"})
    assert r.status_code == 400


def test_non_image_upload_is_rejected(open_client):
    r = open_client.post(
        "/api/generate",
        data={"prompt": "a cat"},
        files={"input_image": ("x.png", b"not an image", "image/png")},
    )
    assert r.status_code == 400


def test_oversized_upload_is_rejected(open_client):
    big = b"\0" * (15 * 1024 * 1024 + 10)
    r = open_client.post("/api/generate", data={"prompt": "a cat"},
                         files={"input_image": ("x.png", big, "image/png")})
    assert r.status_code == 413
