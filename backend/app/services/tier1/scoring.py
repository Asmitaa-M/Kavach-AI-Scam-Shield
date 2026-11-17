"""Hybrid Tier 1 analysis: rules + ML (+ UPI facts). Returns explainable results."""
import re
from dataclasses import dataclass, field, asdict

from app.security.injection import detect_injection
from app.security.redact import redact
from . import classifier
from .rules import LEGIT_SIGNALS, run_rules
from .upi import parse_upi

SUSPICIOUS_TLDS = re.compile(r"\.(xyz|top|click|link|info|online|site|cc|ly)(/|$|\b)", re.I)
BRAND_IN_DOMAIN = re.compile(r"(sbi|hdfc|icici|axis|paytm|phonepe|gpay|npci|rbi|kyc|upi|bank|refund)", re.I)


def level_for(score: int) -> str:
    return "HIGH RISK" if score >= 65 else "SUSPICIOUS" if score >= 35 else "SAFE"


@dataclass
class Indicator:
    id: str
    label: str
    weight: float
    provenance: str = "heuristic"
    matched: str = ""


@dataclass
class Tier1Result:
    score: int
    level: str
    rule_score: float
    ml_prob: float | None
    indicators: list[Indicator] = field(default_factory=list)
    upi: dict | None = None
    notes: list[str] = field(default_factory=list)
    tactics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def blend(rule_score: float, ml_prob: float | None, mode: str = "hybrid") -> float:
    if mode == "rules" or ml_prob is None:
        return rule_score
    if mode == "ml":
        return ml_prob
    hybrid = 0.6 * rule_score + 0.4 * ml_prob
    return max(hybrid, rule_score) if rule_score >= 0.8 else hybrid


def analyze_text(text: str, kind: str = "call", mode: str = "hybrid") -> Tier1Result:
    rr = run_rules(text)
    indicators = [Indicator(h.rule_id, h.label, h.weight, "heuristic", h.matched_text) for h in rr.hits]
    notes: list[str] = []
    upi_dict = None
    extra_weights: list[float] = []

    if kind == "upi":
        facts = parse_upi(text)
        upi_dict = {"upi_ids": facts.upi_ids, "amounts": facts.amounts, "urls": facts.urls,
                    "direction": facts.direction, "direction_note": facts.direction_note}
        if facts.direction == "MONEY_OUT_IF_APPROVED":
            indicators.append(Indicator("direction_out", "Money would leave YOUR account if you approve", 0.40, "verified",
                                        facts.direction_note))
            extra_weights.append(0.40)
        for f in facts.id_findings:
            indicators.append(Indicator("upi_id_pattern", f["label"], f["weight"], "heuristic", f["upi_id"]))
            extra_weights.append(f["weight"])
        for u in facts.urls:
            if SUSPICIOUS_TLDS.search(u) or (BRAND_IN_DOMAIN.search(u) and not re.search(r"(sbi\.co\.in|hdfcbank\.com|icicibank\.com|axisbank\.com|paytm\.com|npci\.org\.in)", u)):
                indicators.append(Indicator("suspicious_url", "Link uses a suspicious domain pattern (not a reputation check)", 0.40, "heuristic", u))
                extra_weights.append(0.40)
        if facts.amounts and max(facts.amounts) >= 10000 and any(i.id == "urgency" for i in indicators):
            indicators.append(Indicator("high_amount_urgency", f"Large amount (₹{max(facts.amounts):,.0f}) combined with urgency", 0.20, "heuristic"))
            extra_weights.append(0.20)

    inj = detect_injection(text)
    if inj:
        indicators.append(Indicator("prompt_injection", "Text tries to instruct the analysis system (manipulation attempt)", 0.50, "heuristic", ", ".join(inj)))
        extra_weights.append(0.50)

    surv = 1.0 - rr.score
    for w in extra_weights:
        surv *= 1.0 - w
    rule_score = round(1.0 - surv, 4)

    p = classifier.predict_proba(redact(text))
    if p is None:
        notes.append("ML model not loaded - using rules only.")
    final = blend(rule_score, p, mode)

    # Genuine-looking transaction wording with no scam tactic hit lowers the score a bit.
    if not indicators and LEGIT_SIGNALS.search(text):
        final *= 0.5
        notes.append("Looks like a routine bank/transaction message (no scam tactics found).")
    if kind == "upi" and upi_dict and upi_dict["direction"] == "MONEY_IN" and not any(
            i.id in {"pin_to_receive", "approve_collect", "wrong_transfer", "credential_request"} for i in indicators):
        final = min(final, 0.30)

    score = int(round(min(1.0, max(0.0, final)) * 100))
    tactics = sorted({h.category for h in rr.hits})
    if len(text.strip()) < 15:
        notes.append("Very short input - analysis may be unreliable.")
    if 35 <= score < 65:
        notes.append("Borderline result - verify independently before acting.")
    return Tier1Result(score, level_for(score), rule_score, p, indicators, upi_dict, notes, tactics)


RECOMMENDATIONS = {
    "upi_trap": "Do NOT approve the request or enter your UPI PIN. You never need a PIN to receive money.",
    "credentials": "Never share OTP, PIN, CVV or passwords with anyone - genuine banks never ask for them.",
    "impersonation": "Hang up and call the person on a number you already have saved. Ask for your family safe word.",
    "secrecy": "A request for secrecy is a red flag. Tell another family member right away.",
    "urgency": "Pressure to act fast is a scam tactic. Take 10 minutes and verify before doing anything.",
    "money_request": "Do not transfer money until you have independently verified who is asking.",
    "remote_access": "Do not install AnyDesk, TeamViewer or any app on a caller's request.",
    "threat": "Police and banks do not demand money over phone to avoid arrest. Hang up.",
    "lure": "Genuine prizes and refunds never require you to pay money or enter a PIN first.",
}


def recommendations_for(result: Tier1Result) -> list[str]:
    cats = {i.id for i in result.indicators} | set(result.tactics)
    order = ["upi_trap", "pin_to_receive", "approve_collect", "credentials", "credential_request", "remote_access",
             "impersonation", "family_impersonation", "official_impersonation", "secrecy", "threat", "lure", "urgency", "money_request"]
    recs, seen = [], set()
    key_map = {"pin_to_receive": "upi_trap", "approve_collect": "upi_trap", "credential_request": "credentials",
               "family_impersonation": "impersonation", "official_impersonation": "impersonation",
               "direction_out": "upi_trap"}
    for k in order + ["direction_out"]:
        if k in cats:
            m = key_map.get(k, k)
            if m in RECOMMENDATIONS and m not in seen:
                seen.add(m)
                recs.append(RECOMMENDATIONS[m])
    if result.level != "SAFE":
        recs.append("If money was already sent, call 1930 (National Cyber Crime Helpline) immediately and report at cybercrime.gov.in.")
    else:
        recs.append("No scam tactics detected. Stay alert - this tool is an aid, not a guarantee.")
    return recs[:5]
