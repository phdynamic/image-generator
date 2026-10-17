import sys
import types

import pytest

from app.main import app
from app.services import generator as generator_module
from app.services import model_manager as manager_module
from app.services.model_manager import ModelManager


@pytest.fixture
def counters(monkeypatch):
    calls = {"clear": 0}
    monkeypatch.setattr(manager_module, "clear_vram", lambda: calls.__setitem__("clear", calls["clear"] + 1))
    monkeypatch.setattr(generator_module, "clear_vram", lambda: calls.__setitem__("clear", calls["clear"] + 1))
    return calls


def test_failed_load_releases_memory_and_resets_state(monkeypatch, counters):
    manager = ModelManager()

    class Half:  # stands in for a partly loaded pipeline
        pass

    monkeypatch.setattr(manager, "_build_pipeline", lambda spec: Half())

    def out_of_memory(pipeline, spec):
        raise RuntimeError("CUDA out of memory. Tried to allocate 2.00 GiB")

    monkeypatch.setattr(manager, "_place", out_of_memory)
    before = counters["clear"]
    with pytest.raises(RuntimeError, match="out of memory"):
        manager.load_model("RunDiffusion/Juggernaut-XL-v9")

    assert manager.pipeline is None and manager.current_model_id is None
    # once when starting the load, and again to undo the half-finished one
    assert counters["clear"] - before >= 2, "VRAM cache should be emptied after a failed load"


def test_failed_generation_releases_memory(monkeypatch, counters):
    fake_torch = types.ModuleType("torch")

    class FakeGenerator:
        def __init__(self, device=None):
            pass

        def manual_seed(self, seed):
            return self

    fake_torch.Generator = FakeGenerator
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    def boom(**kwargs):
        raise RuntimeError("CUDA out of memory")

    gen = app.state.generator
    monkeypatch.setattr(gen.model_manager, "load_model", lambda model_id: None)
    monkeypatch.setattr(gen.model_manager, "get_pipeline", lambda: boom)

    before = counters["clear"]
    with pytest.raises(RuntimeError, match="out of memory"):
        gen.generate(prompt="x", model_id="Lykon/dreamshaper-8", seed=1)
    assert counters["clear"] > before
    assert not gen.lock.locked(), "the generation lock must be released after a failure"
