import gc
import logging
import threading
import traceback

from ..config import settings
from ..utils.gpu_utils import cuda_available, get_device, get_vram_info, clear_vram
from .model_registry import ModelSpec, MODELS, get_spec

logger = logging.getLogger(__name__)

GIB = 1024 ** 3
# Headroom beyond the model's own size for activations and the VAE.
VRAM_HEADROOM_GB = 1.0


class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.current_model_id = None
                cls._instance.pipeline = None
                cls._instance.img2img_pipeline = None
                cls._instance._load_lock = threading.Lock()
            return cls._instance

    def load_model(self, model_id: str):
        spec = get_spec(model_id)
        if spec is None:
            raise ValueError(f"Unknown model: {model_id}")

        with self._load_lock:
            if self.current_model_id == model_id and self.pipeline is not None:
                return

            self.unload_model()

            try:
                pipeline = self._build_pipeline(spec)
                self._place(pipeline, spec)
                self.pipeline = pipeline
                self.img2img_pipeline = self._build_img2img(pipeline)
                self.current_model_id = model_id
            except BaseException as exc:
                # A half-loaded model (e.g. after running out of GPU memory) would
                # otherwise keep its RAM and VRAM until the app restarts.
                traceback.clear_frames(exc.__traceback__)
                self.unload_model()
                raise

    def unload_model(self):
        self.pipeline = None
        self.img2img_pipeline = None
        self.current_model_id = None
        gc.collect()
        clear_vram()

    def get_pipeline(self):
        if self.pipeline is None:
            raise RuntimeError("No model is currently loaded. Call load_model() first.")
        return self.pipeline

    def get_img2img_pipeline(self):
        if self.img2img_pipeline is None:
            raise RuntimeError("Image-to-image isn't available for this model.")
        return self.img2img_pipeline

    # -- downloading --------------------------------------------------------

    def download_model(self, spec: ModelSpec) -> None:
        """Fetch a model's files into the cache without loading it.

        Mirrors what load_model() asks for, so the same files are reused.
        """
        from diffusers import DiffusionPipeline

        common = {"cache_dir": settings.MODELS_CACHE_DIR, "token": settings.HF_TOKEN or None}
        if spec.variant and cuda_available():
            try:
                DiffusionPipeline.download(spec.id, variant=spec.variant, use_safetensors=True, **common)
                return
            except (ValueError, OSError) as exc:
                logger.warning("%s has no '%s' weights (%s); downloading the default files",
                               spec.id, spec.variant, exc)
        DiffusionPipeline.download(spec.id, **common)

    # -- loading ------------------------------------------------------------

    def _build_pipeline(self, spec: ModelSpec):
        token = settings.HF_TOKEN or None

        import torch
        from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline

        use_fp16 = cuda_available()
        kwargs = {
            "torch_dtype": torch.float16 if use_fp16 else torch.float32,
            "cache_dir": settings.MODELS_CACHE_DIR,
            "token": token,
        }
        if spec.family == "sd15":
            # The safety checker reads diffusers source files at runtime,
            # which fails in a PyInstaller bundle, and isn't wanted here.
            kwargs["safety_checker"] = None
            kwargs["requires_safety_checker"] = False
            pipe_cls = StableDiffusionPipeline
        else:
            pipe_cls = StableDiffusionXLPipeline

        if spec.variant and use_fp16:
            try:
                return pipe_cls.from_pretrained(
                    spec.id, variant=spec.variant, use_safetensors=True, **kwargs
                )
            except (ValueError, OSError) as exc:
                logger.warning(
                    "%s has no '%s' weights (%s); using the default files",
                    spec.id, spec.variant, exc,
                )
        return pipe_cls.from_pretrained(spec.id, **kwargs)

    def _place(self, pipeline, spec: ModelSpec):
        if get_device() != "cuda":
            pipeline.to("cpu")
            return

        mode = settings.OFFLOAD.lower()
        vram = get_vram_info()
        free_gb = vram["free"] / GIB if vram else 0.0
        offload = mode == "always" or (
            mode != "never" and free_gb < spec.vram_gb + VRAM_HEADROOM_GB
        )
        logger.info(
            "Loading %s: %.1f GB VRAM free, needs ~%g GB -> %s",
            spec.name, free_gb, spec.vram_gb,
            "CPU offload" if offload else "fully on GPU",
        )

        if offload:
            pipeline.enable_model_cpu_offload()
        else:
            pipeline.to("cuda")

        if spec.family == "sd15":
            pipeline.enable_attention_slicing()
        else:
            # Keeps the VAE decode of large images from spiking VRAM.
            vae = getattr(pipeline, "vae", None)
            if vae is not None and hasattr(vae, "enable_tiling"):
                vae.enable_tiling()

    def _build_img2img(self, pipeline):
        try:
            from diffusers import AutoPipelineForImage2Image
            return AutoPipelineForImage2Image.from_pipe(pipeline)
        except Exception as exc:
            logger.warning("Image-to-image unavailable for this model: %s", exc)
            return None

    @staticmethod
    def get_available_models() -> list[dict]:
        return [m.to_api() for m in MODELS]
