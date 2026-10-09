"""Upload validation and preprocessing. Uploads are handled in memory only."""
import io
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings
from app.errors import AppError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}  # Pillow's names for jpg/jpeg, png, webp
MAX_PIXELS = 40_000_000  # reject decompression bombs
MODEL_MAX_SIDE = 512  # CLIP downsizes to 224 anyway; no need to keep full-size copies

MSG_INVALID = "Please upload a valid jewellery image."


def _too_large(limit: int) -> AppError:
    mb = limit / (1024 * 1024)
    return AppError("IMAGE_TOO_LARGE", f"Image file is too large. Maximum allowed size is {mb:g} MB.", 413)


def read_limited(fileobj: BinaryIO, max_bytes: int | None = None) -> bytes:
    """Read an upload, refusing anything larger than the limit without buffering it all."""
    limit = max_bytes or settings.max_image_bytes
    data = fileobj.read(limit + 1)
    if len(data) > limit:
        raise _too_large(limit)
    return data


def validate_image(
    data: bytes,
    max_bytes: int | None = None,
    max_width: int | None = None,
    max_height: int | None = None,
) -> Image.Image:
    """Check the real image content (never the extension) and return a loaded image."""
    limit = max_bytes or settings.max_image_bytes
    max_w = max_width or settings.max_search_image_width
    max_h = max_height or settings.max_search_image_height

    if not data:
        raise AppError("INVALID_IMAGE", MSG_INVALID, 400)
    if len(data) > limit:
        raise _too_large(limit)
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in ALLOWED_FORMATS:
                raise AppError(
                    "UNSUPPORTED_FORMAT",
                    "Unsupported image format. Please use JPG, PNG or WebP.",
                    415,
                )
            width, height = probe.size
            if width < 1 or height < 1 or width * height > MAX_PIXELS:
                raise AppError("INVALID_IMAGE", MSG_INVALID, 400)
            if width > max_w or height > max_h:
                raise AppError(
                    "IMAGE_DIMENSIONS_TOO_LARGE",
                    f"Image dimensions ({width}x{height}) exceed maximum allowed limit of {max_w}x{max_h} pixels.",
                    413,
                )
            probe.verify()  # detects truncated/corrupt files; invalidates `probe`
        image = Image.open(io.BytesIO(data))
        image.load()
        return image
    except AppError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise AppError("INVALID_IMAGE", MSG_INVALID, 400) from None


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """Apply EXIF rotation and flatten transparency onto white (common for product PNGs)."""
    image = ImageOps.exif_transpose(image)
    has_alpha = image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def resize_for_model(image: Image.Image, max_side: int = MODEL_MAX_SIDE) -> Image.Image:
    """Shrink (never enlarge) so the longest side is at most `max_side`."""
    resized = image.copy()
    resized.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return resized


def prepare_for_model(image: Image.Image) -> Image.Image:
    """The single preprocessing path shared by indexing and search."""
    return resize_for_model(convert_to_rgb(image))
