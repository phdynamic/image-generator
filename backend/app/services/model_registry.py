"""The models Imaginaree can load.

Adding a model is one entry here. Only models listed here can be requested,
so a client can never make the server download an arbitrary repository.
"""
from dataclasses import dataclass, asdict
from typing import Literal

Family = Literal["sd15", "sdxl"]


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    family: Family
    vram_gb: float
    description: str
    default_steps: int = 30
    default_cfg: float = 7.5
    default_size: int = 512
    max_steps: int = 50
    # Models trained without classifier-free guidance ignore the CFG slider.
    fixed_cfg: float | None = None
    supports_negative: bool = True
    # Try this weights variant first and fall back to the default files.
    variant: str | None = None
    experimental: bool = False
    gated: bool = False
    download_gb: float | None = None
    # Smallest GPU (total memory) the model can run on; 0 means no requirement.
    min_vram_gb: float = 0

    def to_api(self) -> dict:
        data = asdict(self)
        data["type"] = self.family
        data["vram"] = f"{self.vram_gb:g} GB"
        return data


MODELS: list[ModelSpec] = [
    ModelSpec(
        id="Lykon/dreamshaper-8",
        name="DreamShaper 8",
        family="sd15",
        vram_gb=4,
        description="Fast and versatile. Good for illustrations and quick drafts.",
        default_steps=30,
        default_cfg=7.5,
        default_size=512,
    ),
    ModelSpec(
        id="RunDiffusion/Juggernaut-XL-v9",
        name="Juggernaut XL v9",
        family="sdxl",
        vram_gb=7,
        description="SDXL fine-tune. Detailed, photorealistic scenes and people.",
        default_steps=30,
        default_cfg=5.0,
        default_size=1024,
        variant="fp16",
        download_gb=7,
    ),
    ModelSpec(
        id="SG161222/RealVisXL_V5.0",
        name="RealVisXL V5.0",
        family="sdxl",
        vram_gb=7,
        description="SDXL fine-tune. Natural, realistic photos for training scenarios.",
        default_steps=30,
        default_cfg=5.0,
        default_size=1024,
        variant="fp16",
        download_gb=7,
    ),
    ModelSpec(
        id="segmind/SSD-1B",
        name="Segmind SSD-1B",
        family="sdxl",
        vram_gb=5,
        description="Distilled SDXL. Faster and lighter, good detail.",
        default_steps=30,
        default_cfg=7.5,
        default_size=1024,
    ),
    ModelSpec(
        id="stabilityai/sdxl-turbo",
        name="SDXL Turbo",
        family="sdxl",
        vram_gb=6,
        description="Near-instant drafts in 1-4 steps. Ignores CFG and negative prompts.",
        default_steps=4,
        default_cfg=0.0,
        default_size=512,
        max_steps=8,
        fixed_cfg=0.0,
        supports_negative=False,
    ),
]

_BY_ID = {m.id: m for m in MODELS}


def get_spec(model_id: str) -> ModelSpec | None:
    return _BY_ID.get(model_id)


def gpu_problem(spec: ModelSpec, total_vram_bytes: int | None) -> str | None:
    """Why this model can't run on this GPU, or None if it can."""
    if not spec.min_vram_gb:
        return None
    if total_vram_bytes is None:
        return f"{spec.name} needs an NVIDIA GPU with about {spec.min_vram_gb:g} GB of memory."
    total_gb = total_vram_bytes / 1024 ** 3
    # Cards report a little under their nominal size (a "12 GB" card shows ~11.6).
    if total_gb >= spec.min_vram_gb - 0.75:
        return None
    return (f"{spec.name} needs a GPU with about {spec.min_vram_gb:g} GB of memory; "
            f"this one has {total_gb:.1f} GB.")
