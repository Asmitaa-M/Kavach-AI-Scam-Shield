"""Explainable rule engine (Tier 1, runs locally in the backend process).

Each rule maps to a scam-tactic category. Patterns cover English, Tamil script,
Tanglish (romanised Tamil) and Hinglish. Negation guards stop warning text such as
"never share your OTP" (common in genuine bank SMS) from being flagged as a scam.
"""
import re
from dataclasses import dataclass, field

I = re.I


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    label: str
    weight: float          # contribution to noisy-OR score
    pattern: re.Pattern
    negatable: bool = False  # skip when preceded by "do not / never / வேண்டாம்"


def R(id_, cat, label, w, pat, negatable=False):
    return Rule(id_, cat, label, w, re.compile(pat, I), negatable)


RULES: list[Rule] = [
    R("urgency", "urgency", "Pressure to act immediately", 0.30,
      r"\b(urgent(ly)?|immediately|right now|asap|at once|within \d+ ?(min|minutes|hours|hrs)|hurry|last chance|before it'?s too late)\b"
      r"|உடனே|அவசரம்|உடனடியாக|இப்போதே|\b(udane|udanadiyaga|avasaram|avasarama|ippove|ippodhe)\b"
      r"|तुरंत|अभी|जल्दी|\b(turant|abhi|jaldi)\b"),
    R("money_request", "money_request", "Request to send/transfer money", 0.30,
      r"\b(send|transfer|pay|deposit|wire|gpay|phonepe|paytm)\b.{0,40}(₹|rs\.?|rupees|inr|\d{3,})"
      r"|(₹|rs\.?|inr)\s?\d[\d,]*.{0,30}\b(send|transfer|pay|needed|need|required)\b"
      r"|பணம்.{0,20}(அனுப்பு|அனுப்புங்க|தேவை)|\b(panam|paisa|paise)\b.{0,25}\b(anuppu\w*|anupunga|bhej\w*|venum)\b"
      r"|\b(venum|chahiye)\b.{0,20}(₹|rs|rupees|\d{3,})"),
    R("secrecy", "secrecy", "Asks you to keep it secret", 0.45,
      r"(don'?t|do not|dont|never)\s+(tell|inform|say|share this with)\s+(anyone|anybody|mom|dad|mummy|papa|amma|appa|family|your (wife|husband|son|daughter))"
      r"|keep (this|it) (a )?(secret|between us|confidential)|(யாரிடமும்|யார்கிட்டயும்).{0,15}(சொல்ல|சொல்லாத)"
      r"|\b(yaarkittayum|yarukitayum|yaaridamum)\b.{0,15}\b(solla|sollathe|solladha)\w*"
      r"|kisi ko (mat|na) (batana|batao|bolna)"),
    R("credential_request", "credentials", "Asks for OTP / PIN / password / CVV", 0.60,
      r"(share|send|tell|give|provide|enter|read( out)?|say|forward|sollunga|batao|bataiye|சொல்லுங்கள்|சொல்லுங்க|அனுப்புங்கள்).{0,30}\b(otp|upi ?pin|atm ?pin|pin|cvv|password|passcode|ஓடிபி|ஒடிபி)\b"
      r"|\b(otp|pin|cvv|password|ஓடிபி)\b.{0,25}(share|send|tell|give|provide|read|sollunga|batao|சொல்லுங்கள்|சொல்லுங்க)",
      negatable=True),
    R("family_impersonation", "impersonation", "Claims a relative is in trouble / is a relative", 0.40,
      r"\b(your|ur)\s+(son|daughter|grandson|granddaughter|nephew|niece|brother|husband|wife)\b.{0,50}\b(accident|hospital|arrest(ed)?|jail|police|kidnap\w*|trouble|emergency|injur\w*|serious)\b"
      r"|\b(papa|dad|mom|mummy|amma|appa|nana|nani|dadi|dada)\b.{0,40}\b(i'?m|i am|main|naan)\b.{0,30}\b(trouble|accident|arrest\w*|hospital|emergency|jail)\b"
      r"|\b(this is (my )?new number|my phone (is )?(broke|broken|lost|stolen)|lost my phone)\b"
      r"|உங்க(ள்)? (மகன்|மகள்|பேரன்|பேத்தி).{0,40}(விபத்து|கைது|மருத்துவமனை|ஆபத்து)"
      r"|\b(unga|ungal)\s+(magan|maganukku|magal|peran)\b.{0,40}\b(accident|arrest|hospital|aapathu|vibathu)\b"
      r"|\b(beta|bete|aapka (beta|bhai))\b.{0,40}\b(accident|arrest|hospital|police)\b"
      r"|\b(naan|nan)\s+(unga|ungal)\s+(magan|maganukku|magal)\b"),
    R("official_impersonation", "impersonation", "Poses as bank / police / government official", 0.35,
      r"\b(bank (officer|manager|executive)|rbi|reserve bank|cbi|ncb|narcotics|customs|income tax|trai|cyber ?crime (police|cell)|police (officer|station)|court|ed officer|sbi (kyc|officer)|your kyc)\b"
      r"|வங்கி அதிகாரி|போலீஸ்|சுங்கத்துறை"),
    R("threat", "threat", "Threat of arrest / legal action / account block", 0.40,
      r"\b(arrest(ed)?|digital arrest|fir\b|legal action|warrant|case (will be|has been)|account (will be|is|has been) (blocked|suspended|closed|frozen)|sim (will be|is) (blocked|deactivated)|your (account|sim|card) (is |will be )?(blocked|suspended|deactivated))\b"
      r"|கைது|வழக்கு|கணக்கு (முடக்க|நிறுத்த)"),
    R("remote_access", "remote_access", "Asks to install a remote-access / unknown app", 0.55,
      r"\b(anydesk|teamviewer|quick ?support|airdroid|rustdesk|screen ?share|remote (access|support)|install (this|the) (app|apk)|download (this|the) (app|apk)|\.apk)\b"
      r"|ஆப்.{0,15}(இன்ஸ்டால்|நிறுவ)"),
    R("prize_refund", "lure", "Prize / lottery / refund lure", 0.35,
      r"\b(lottery|you (have )?won|prize|lucky draw|cashback (of|worth)|refund (of|is|will)|kbc|claim (your )?(reward|prize|refund))\b|பரிசு|லாட்டரி"),
    R("wrong_transfer", "lure", "'Sent by mistake - please return' pattern", 0.50,
      r"\b(sent|transferred|credited|paid)\b.{0,40}\b(by mistake|wrongly|wrong number|wrong account|accidentally)\b.{0,60}\b(return|send (it )?back|refund|revert)\b"
      r"|\b(by mistake|wrongly|accidentally)\b.{0,40}\b(return|send (it )?back|refund|revert)\b"
      r"|தவறுதலாக.{0,40}(திருப்பி|அனுப்பு)"),
    # ---- UPI-specific tactics ----
    R("pin_to_receive", "upi_trap", "Says UPI PIN is needed to RECEIVE money (never true)", 0.85,
      r"\b(enter|put|type|share|give)\b.{0,25}\b(upi ?)?pin\b.{0,35}\b(to )?(receive|get|claim|credit|accept)\b"
      r"|\b(to )?(receive|get|claim)\b.{0,40}\b(enter|put|type)\b.{0,15}\b(upi ?)?pin\b"
      r"|\bpin\b.{0,15}\b(required|needed|zaroori|venum)\b.{0,20}\b(receive|refund|credit)\b"),
    R("approve_collect", "upi_trap", "Asks you to approve/accept a collect request", 0.55,
      r"\b(approve|accept|authori[sz]e|confirm)\b.{0,30}\b(collect|request|mandate|payment request|upi request)\b"
      r"|\b(collect|money|payment) request\b.{0,30}\b(approve|accept|authori[sz]e)\b"
      r"|\bscan\b.{0,30}\b(qr|code)\b.{0,30}\b(receive|get|refund|claim)\b"),
]

_NEGATION = re.compile(
    r"(do not|don'?t|dont|never|not|no one|nobody|mat|nahi|வேண்டாம்|யாருடனும்|"
    r"warns?|beware|fraud(sters)?|scam)\W+(\w+\W+){0,6}$", I)


@dataclass
class RuleHit:
    rule_id: str
    category: str
    label: str
    weight: float
    matched_text: str
    provenance: str = "heuristic"


@dataclass
class RuleResult:
    hits: list[RuleHit] = field(default_factory=list)
    score: float = 0.0  # 0..1


def _negated(text: str, start: int) -> bool:
    window = text[max(0, start - 60):start]
    return bool(_NEGATION.search(window))


def run_rules(text: str) -> RuleResult:
    hits: list[RuleHit] = []
    seen: set[str] = set()
    for rule in RULES:
        for m in rule.pattern.finditer(text):
            if rule.negatable and _negated(text, m.start()):
                continue
            if rule.id in seen:
                break
            seen.add(rule.id)
            hits.append(RuleHit(rule.id, rule.category, rule.label, rule.weight,
                                text[m.start():m.end()][:80].strip()))
            break
    survive = 1.0
    for h in hits:
        survive *= 1.0 - h.weight
    score = 1.0 - survive
    # Co-occurrence boosts: tactics that rarely appear together in legitimate messages.
    ids = {h.rule_id for h in hits}
    if {"money_request", "urgency"} <= ids and ({"secrecy", "family_impersonation"} & ids):
        score = min(1.0, score + 0.15)
    if "family_impersonation" in ids and "money_request" in ids:
        score = min(1.0, score + 0.10)
    if {"official_impersonation", "threat"} <= ids:
        score = min(1.0, score + 0.10)
    return RuleResult(hits, round(score, 4))


LEGIT_SIGNALS = re.compile(
    r"\b(has been credited|credited to (your )?a/?c|debited from your a/?c|"
    r"is your (otp|one[- ]time)|otp (is|for)|do not share|never share|"
    r"txn(\s|id|:)|ref(erence)? (no|number)|available bal)\b|பெறப்பட்டது", I)
