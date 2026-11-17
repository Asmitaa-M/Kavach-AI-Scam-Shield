"""Redact sensitive data before it is stored, logged or sent to a third party."""
import re

_PATTERNS = [
    (re.compile(r"(?i)\b(otp|pin|cvv|password|passcode)\b(\s*(is|:|=|-)?\s*)\d{3,8}\b"), r"\1\2[REDACTED]"),
    (re.compile(r"\b\d{12,19}\b"), "[NUMBER-REDACTED]"),            # card / account numbers
    (re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)"), "[PHONE-REDACTED]"),
    (re.compile(r"(?i)\b[A-Z]{4}0[A-Z0-9]{6}\b"), "[IFSC-REDACTED]"),
]


def redact(text: str) -> str:
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text
