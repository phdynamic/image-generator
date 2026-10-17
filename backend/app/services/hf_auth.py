"""Whether a HuggingFace token is available for downloading gated models."""
from ..config import settings


def hf_token_available() -> bool:
    if settings.HF_TOKEN:
        return True
    try:  # a token saved by `huggingface-cli login` also works
        from huggingface_hub import get_token
        return bool(get_token())
    except Exception:
        return False


def gated_message(model_id: str, token_set: bool) -> str:
    url = f"https://huggingface.co/{model_id}"
    if token_set:
        return (f"HuggingFace refused access to this model. Open {url} and accept its terms while "
                "signed in to the same account that owns your token, and check the token has Read access.")
    return (f"This model needs a free HuggingFace token. (1) Sign in at huggingface.co and accept the "
            f"terms at {url}. (2) Create a Read token at huggingface.co/settings/tokens. "
            "(3) Add HF_TOKEN=... to the .env file and restart Imaginaree.")
