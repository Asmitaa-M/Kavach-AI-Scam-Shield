"""Screenshot OCR via Tesseract. Uses Tamil/Hindi packs when installed, else English only."""
import io
import subprocess
from functools import lru_cache

import pytesseract
from PIL import Image, UnidentifiedImageError


@lru_cache
def _langs() -> str:
    try:
        out = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=10).stdout.split()
    except Exception:
        return "eng"
    want = [l for l in ("eng", "tam", "hin") if l in out]
    return "+".join(want) or "eng"


def extract_text(data: bytes) -> tuple[str, str]:
    """Returns (text, languages_used). Raises ValueError on unreadable images."""
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data)).convert("L")
        if img.width * img.height > 25_000_000:
            raise ValueError("Image resolution too large")
    except (UnidentifiedImageError, OSError) as e:
        raise ValueError("Could not read image") from e
    langs = _langs()
    return pytesseract.image_to_string(img, lang=langs).strip(), langs
