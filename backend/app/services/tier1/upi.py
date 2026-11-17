"""UPI-specific parsing: UPI IDs, amounts, URLs and payment DIRECTION.

Direction matters: a *collect request* pulls money OUT of the victim's account,
while a *credit* message is informational. Scammers blur the two.
"""
import re
from dataclasses import dataclass, field

KNOWN_HANDLES = {
    "oksbi", "okhdfcbank", "okaxis", "okicici", "ybl", "ibl", "axl", "paytm", "apl",
    "upi", "sbi", "hdfcbank", "icici", "axisbank", "kotak", "pnb", "boi", "cnrb",
    "idfcbank", "yesbank", "indus", "federal", "fbl", "airtel", "jio", "pingpay",
    "postbank", "unionbank", "canarabank", "sib", "rbl", "freecharge", "slice",
}
_UPI_ID = re.compile(r"(?<![\w.\-])([a-z0-9][a-z0-9._\-]{1,60})@([a-z][a-z0-9]{1,30})(?!\w)(?!\.[a-z0-9])", re.I)
_URL = re.compile(r"(?i)\b((?:https?://|www\.)[^\s<>\"')]+|(?:[a-z0-9\-]+\.)+(?:com|in|co\.in|net|org|xyz|top|click|link|info|online|site|ly|cc|app|me)(?:/[^\s<>\"')]*)?)")
_AMOUNT = re.compile(r"(?:₹|rs\.?|inr|rupees)\s?([\d,]+(?:\.\d{1,2})?)|([\d,]+(?:\.\d{1,2})?)\s?(?:rupees|rs\b|/-)", re.I)

_REQUEST = re.compile(
    r"\b(collect request|money request|payment request|requested?|is requesting|requests? (you )?(for|to pay)|"
    r"wants? (to )?(collect|receive)|has (sent|raised) (you )?a (collect|payment|money)|pay (₹|rs)|"
    r"approve|authori[sz]e|to pay)\b|கோரிக்கை", re.I)
_CREDIT = re.compile(
    r"\b(credited|received|deposited|has been added|added to your|sent you|paid you)\b|பெறப்பட்டது|வரவு", re.I)
_DEBIT = re.compile(r"\b(debited|deducted|paid to|sent to|transferred to)\b|கழிக்கப்பட்டது", re.I)

SUSPICIOUS_ID_WORDS = re.compile(
    r"(refund|support|care|help|kyc|lottery|reward|prize|cashback|bank|official|customer|verify|claim|offer|winner)", re.I)


@dataclass
class UpiFacts:
    upi_ids: list[str] = field(default_factory=list)
    amounts: list[float] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    direction: str = "UNKNOWN"  # MONEY_OUT_IF_APPROVED | MONEY_IN | MONEY_OUT_DONE | UNKNOWN
    direction_note: str = ""
    id_findings: list[dict] = field(default_factory=list)


def extract_amounts(text: str) -> list[float]:
    out = []
    for m in _AMOUNT.finditer(text):
        raw = (m.group(1) or m.group(2) or "").replace(",", "")
        try:
            out.append(float(raw))
        except ValueError:
            pass
    return out


def analyze_upi_id(upi_id: str) -> list[dict]:
    """Pure pattern analysis. This is NOT a reputation lookup."""
    local, _, handle = upi_id.lower().partition("@")
    findings = []
    if handle not in KNOWN_HANDLES:
        findings.append({"label": f"Unrecognised UPI handle '@{handle}'", "weight": 0.25})
    if SUSPICIOUS_ID_WORDS.search(local):
        findings.append({"label": "UPI ID contains official/lure wording (e.g. refund, support, kyc)", "weight": 0.35})
    if len(re.findall(r"\d", local)) >= 6 and not local.isdigit():
        findings.append({"label": "UPI ID has many random digits", "weight": 0.15})
    if re.search(r"(sbi|hdfc|icici|axis|paytm|phonepe|gpay|npci|rbi)", local) and handle not in {"sbi", "hdfcbank", "icici", "axisbank", "paytm", "oksbi", "okhdfcbank", "okaxis", "okicici"}:
        findings.append({"label": "Brand name in UPI ID but handle does not belong to that brand (impersonation pattern)", "weight": 0.40})
    return findings


def parse_upi(text: str) -> UpiFacts:
    f = UpiFacts()
    f.upi_ids = list(dict.fromkeys(m.group(0).lower() for m in _UPI_ID.finditer(text)
                                   if "." not in m.group(2)))
    f.amounts = extract_amounts(text)
    f.urls = list(dict.fromkeys(u.rstrip(".,;)") for u in (m.group(1) for m in _URL.finditer(text))
                                if "@" not in u and u.lower() not in {i.split("@")[1] for i in f.upi_ids}))
    for uid in f.upi_ids:
        for fnd in analyze_upi_id(uid):
            f.id_findings.append({"upi_id": uid, **fnd})

    asks = bool(_REQUEST.search(text))
    credit = bool(_CREDIT.search(text))
    debit = bool(_DEBIT.search(text))
    if asks and not credit:
        f.direction = "MONEY_OUT_IF_APPROVED"
        f.direction_note = "This is a REQUEST. Approving it and entering your PIN sends money FROM your account."
    elif credit and not asks:
        f.direction = "MONEY_IN"
        f.direction_note = "Wording suggests money was received. Receiving money never needs your PIN."
    elif debit and not asks:
        f.direction = "MONEY_OUT_DONE"
        f.direction_note = "Wording suggests money has already left your account."
    elif asks and credit:
        f.direction = "MONEY_OUT_IF_APPROVED"
        f.direction_note = ("Mixed wording: mentions receiving money but also asks you to approve something. "
                            "This blur is a classic scam trick - treat it as money going OUT.")
    return f
