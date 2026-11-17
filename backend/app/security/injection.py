"""Prompt-injection hygiene for untrusted text that reaches an LLM.

Principles: (1) untrusted text is DATA inside a delimited block, (2) the LLM has no
tool authority, (3) outputs are schema-validated, (4) injection attempts are themselves
reported as scam evidence.
"""
import re

_INJECTION = [
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)",
    r"disregard (the )?(system|previous) (prompt|instructions)",
    r"you are now", r"system prompt", r"reveal (your )?(prompt|instructions|key)",
    r"mark (this )?(as )?(safe|legit)", r"risk[_ ]?score\s*[:=]\s*\d+",
    r"</?(system|assistant|untrusted)>",
]
_RX = re.compile("|".join(_INJECTION), re.I)


def detect_injection(text: str) -> list[str]:
    return sorted({m.group(0).lower() for m in _RX.finditer(text)})


def wrap_untrusted(text: str, max_len: int = 4000) -> str:
    cleaned = text[:max_len].replace("<untrusted>", "").replace("</untrusted>", "")
    return f"<untrusted>\n{cleaned}\n</untrusted>"
