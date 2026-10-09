import io

import pytest
from PIL import Image

from app.errors import AppError
from app.utils.image_utils import convert_to_rgb, resize_for_model, validate_image
from tests.conftest import make_image_bytes


def test_accepts_png_jpeg_webp():
    for fmt in ("PNG", "JPEG", "WEBP"):
        img = validate_image(make_image_bytes(fmt))
        assert img.size == (64, 64)


def test_rejects_non_image_bytes():
    with pytest.raises(AppError) as exc:
        validate_image(b"this is not an image")
    assert exc.value.code == "INVALID_IMAGE"


def test_rejects_empty_upload():
    with pytest.raises(AppError) as exc:
        validate_image(b"")
    assert exc.value.code == "INVALID_IMAGE"


def test_rejects_unsupported_format():
    with pytest.raises(AppError) as exc:
        validate_image(make_image_bytes("GIF"))
    assert exc.value.code == "UNSUPPORTED_FORMAT"
    assert exc.value.status_code == 415


def test_rejects_truncated_file():
    data = make_image_bytes("PNG", size=(300, 300))
    with pytest.raises(AppError) as exc:
        validate_image(data[: len(data) // 2])
    assert exc.value.code == "INVALID_IMAGE"


def test_rejects_oversized_upload():
    with pytest.raises(AppError) as exc:
        validate_image(b"\0" * 2048, max_bytes=1024)
    assert exc.value.code == "IMAGE_TOO_LARGE"
    assert exc.value.status_code == 413


def test_extension_is_ignored_content_is_checked():
    # A text file is rejected no matter what it is called; validation only sees bytes.
    with pytest.raises(AppError):
        validate_image(b"GIF89a-not-really")


def test_transparent_png_is_flattened_on_white():
    rgba = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    out = convert_to_rgb(rgba)
    assert out.mode == "RGB"
    assert out.getpixel((5, 5)) == (255, 255, 255)


def test_resize_never_enlarges_and_caps_longest_side():
    big = Image.new("RGB", (2000, 1000))
    small = Image.new("RGB", (100, 80))
    assert max(resize_for_model(big, 512).size) == 512
    assert resize_for_model(small, 512).size == (100, 80)
    assert big.size == (2000, 1000)  # original untouched


def test_roundtrip_through_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (30, 30), (1, 2, 3)).save(buf, "JPEG")
    assert validate_image(buf.getvalue()).mode in ("RGB", "L")
