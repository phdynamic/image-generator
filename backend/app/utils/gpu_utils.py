try:
    import torch
except ImportError:  # lets the API start (e.g. in tests) without PyTorch
    torch = None


def cuda_available() -> bool:
    return torch is not None and torch.cuda.is_available()


def get_device() -> str:
    return "cuda" if cuda_available() else "cpu"


def get_gpu_name() -> str | None:
    if not cuda_available():
        return None
    return torch.cuda.get_device_name(0)


def get_vram_info() -> dict | None:
    """System-wide VRAM, so memory used by other programs is counted."""
    if not cuda_available():
        return None
    free, total = torch.cuda.mem_get_info(0)
    return {"total": total, "used": total - free, "free": free}


def clear_vram():
    if cuda_available():
        torch.cuda.empty_cache()
