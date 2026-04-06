import torch


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def get_vram_info() -> dict | None:
    if not torch.cuda.is_available():
        return None
    total = torch.cuda.get_device_properties(0).total_memory
    used = torch.cuda.memory_allocated(0)
    free = total - used
    return {"total": total, "used": used, "free": free}


def clear_vram():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
