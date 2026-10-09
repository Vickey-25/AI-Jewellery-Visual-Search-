"""OpenCLIP wrapper. The model is loaded once and shared by every request."""
import logging
import threading

import numpy as np
import open_clip
import torch
from PIL import Image

logger = logging.getLogger(__name__)


def resolve_device(requested: str) -> str:
    """'cpu' forces CPU. Anything else uses CUDA only if it is actually available."""
    if (requested or "").lower() == "cpu":
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


class CLIPService:
    def __init__(
        self,
        model_name: str = "ViT-B-32",
        pretrained: str = "laion2b_s34b_b79k",
        device: str = "cpu",
        num_threads: int | None = None,
    ) -> None:
        if num_threads:
            torch.set_num_threads(num_threads)
        self.device = resolve_device(device)
        self.model_name = model_name
        self.pretrained = pretrained
        logger.info("AI Device: %s", self.device.upper())
        logger.info("Loading OpenCLIP %s (%s)...", model_name, pretrained)
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.model.eval()
        # One inference at a time keeps CPU usage predictable on a small laptop.
        self._lock = threading.Lock()

    @property
    def embedding_dim(self) -> int:
        return int(self.model.visual.output_dim)

    @staticmethod
    def _to_unit_numpy(features: torch.Tensor) -> np.ndarray:
        features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().astype("float32")

    def generate_image_embedding(self, image: Image.Image) -> np.ndarray:
        """Return a normalised float32 vector of shape (dim,)."""
        tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        with self._lock, torch.inference_mode():
            features = self.model.encode_image(tensor)
        return self._to_unit_numpy(features)[0]

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Return a normalised float32 vector in the same space as the image embeddings."""
        tokens = self.tokenizer([text]).to(self.device)
        with self._lock, torch.inference_mode():
            features = self.model.encode_text(tokens)
        return self._to_unit_numpy(features)[0]
