"""Argon2id hashing for passwords and family phrases + JWT helpers."""
import hmac
import unicodedata
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.config import get_settings

_ph = PasswordHasher()  # argon2id, per-hash random salt


def hash_password(pw: str) -> str:
    return _ph.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, pw)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def normalize_phrase(phrase: str) -> str:
    """Case/whitespace-insensitive so 'Blue  mango 27' matches 'blue mango 27'."""
    return " ".join(unicodedata.normalize("NFKC", phrase).casefold().split())


def hash_phrase(phrase: str) -> str:
    return _ph.hash(normalize_phrase(phrase))


def verify_phrase(phrase: str, hashed: str) -> bool:
    # argon2-cffi performs its own constant-time comparison of digests.
    try:
        return _ph.verify(hashed, normalize_phrase(phrase))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_token(user_id: str) -> str:
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=s.jwt_expire_minutes)
    return jwt.encode({"sub": user_id, "exp": exp}, s.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        data = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        return data.get("sub")
    except jwt.PyJWTError:
        return None


def safe_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
