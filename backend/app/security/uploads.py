"""Safe upload validation: size cap + magic-byte sniffing (never trust client MIME)."""
from fastapi import HTTPException, UploadFile
from app.config import get_settings

_MAGIC = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "webp": b"RIFF",
}
_AUDIO_MAGIC = {"wav": b"RIFF", "mp3a": b"ID3", "mp3b": b"\xff\xfb", "ogg": b"OggS", "flac": b"fLaC"}


async def read_validated(file: UploadFile, kind: str) -> bytes:
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"File too large (max {limit // 1024 // 1024} MB)")
    if not data:
        raise HTTPException(400, "Empty file")
    table = _MAGIC if kind == "image" else _AUDIO_MAGIC
    if not any(data.startswith(m) for m in table.values()):
        raise HTTPException(415, f"Unsupported or corrupted {kind} file")
    return data
