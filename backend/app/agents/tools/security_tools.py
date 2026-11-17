"""Investigation tools. Contract: every tool returns a ToolResult and NEVER raises or invents data.
status: ok | unavailable (no key / no network / lookup failed) | error.
provenance: 'verified' only when the fact comes from an external API, the database or a deterministic parse."""
import base64
import ipaddress
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.services.tier1.scoring import analyze_text
from app.services.tier1.upi import analyze_upi_id, parse_upi

TIMEOUT = 6.0


@dataclass
class ToolResult:
    tool: str
    status: str                      # ok | unavailable | error
    provenance: str                  # verified | heuristic | unavailable
    summary: str
    findings: list[dict] = field(default_factory=list)   # {description, weight}
    data: dict = field(default_factory=dict)
    followups: list[tuple[str, dict]] = field(default_factory=list)
    ms: int = 0


def _unavailable(tool: str, why: str) -> ToolResult:
    return ToolResult(tool, "unavailable", "unavailable", f"Check not performed: {why}")


def timed(fn):
    def wrap(*a, **k):
        t0 = time.perf_counter()
        try:
            r = fn(*a, **k)
        except Exception as e:  # tools must never crash the investigation
            r = ToolResult(fn.__name__, "error", "unavailable", f"Tool failed ({type(e).__name__}). Result ignored.")
        r.ms = int((time.perf_counter() - t0) * 1000)
        return r
    wrap.__name__ = fn.__name__
    return wrap


def _host(url: str) -> str:
    u = url if re.match(r"https?://", url, re.I) else "http://" + url
    return (urlparse(u).hostname or "").lower()


@timed
def suspicious_language(text: str, kind: str = "call", **_) -> ToolResult:
    res = analyze_text(text, kind)
    findings = [{"description": i.label + (f" ('{i.matched[:50]}')" if i.matched else ""), "weight": i.weight} for i in res.indicators]
    return ToolResult("suspicious_language", "ok", "heuristic",
                      f"Rules+ML scored {res.score}/100 ({res.level}).", findings,
                      {"score": res.score, "level": res.level, "tactics": res.tactics, "ml_prob": res.ml_prob})


@timed
def upi_id_analyzer(text: str, **_) -> ToolResult:
    facts = parse_upi(text)
    fs = [{"description": f"{u}: {x['label']}", "weight": x["weight"]} for u in facts.upi_ids for x in analyze_upi_id(u)]
    summ = f"{len(facts.upi_ids)} UPI ID(s) found; pattern analysis only - NOT a reputation lookup."
    return ToolResult("upi_id_analyzer", "ok", "heuristic", summ, fs,
                      {"upi_ids": facts.upi_ids, "amounts": facts.amounts, "direction": facts.direction,
                       "direction_note": facts.direction_note})


@timed
def url_lexical_check(url: str, **_) -> ToolResult:
    host = _host(url)
    fs = []
    if not host:
        return ToolResult("url_lexical_check", "error", "unavailable", "Could not parse URL.")
    try:
        ipaddress.ip_address(host); fs.append({"description": "URL uses a raw IP address instead of a domain", "weight": 0.40})
    except ValueError:
        pass
    if host.startswith("xn--") or ".xn--" in host:
        fs.append({"description": "Punycode domain (possible look-alike characters)", "weight": 0.35})
    if re.search(r"\.(xyz|top|click|link|info|online|site|cc|ly|buzz|icu)$", host):
        fs.append({"description": "Low-trust top-level domain often used in scams", "weight": 0.25})
    if re.search(r"(sbi|hdfc|icici|axis|paytm|phonepe|npci|rbi|kyc|refund|upi)", host) and not re.search(
            r"(^|\.)(sbi\.co\.in|onlinesbi\.sbi|hdfcbank\.com|icicibank\.com|axisbank\.com|paytm\.com|phonepe\.com|npci\.org\.in|rbi\.org\.in)$", host):
        fs.append({"description": f"Brand/KYC keyword in a domain that is not the brand's known domain ({host})", "weight": 0.40})
    if host.count("-") >= 2:
        fs.append({"description": "Domain has multiple hyphens (common in phishing)", "weight": 0.15})
    if url.lower().startswith("http://"):
        fs.append({"description": "Link is not HTTPS", "weight": 0.10})
    return ToolResult("url_lexical_check", "ok", "heuristic", f"Lexical analysis of {host} (no reputation lookup).", fs, {"host": host},
                      followups=[("domain_whois", {"url": url}), ("safe_browsing", {"url": url}), ("virustotal", {"url": url})])


@timed
def domain_whois(url: str, **_) -> ToolResult:
    host = _host(url)
    parts = host.split(".")
    domain = ".".join(parts[-3:]) if host.endswith((".co.in", ".org.in", ".gov.in", ".co.uk")) else ".".join(parts[-2:])
    try:
        r = httpx.get(f"https://rdap.org/domain/{domain}", timeout=TIMEOUT, follow_redirects=True)
    except httpx.HTTPError:
        return _unavailable("domain_whois", "RDAP service not reachable from this server")
    if r.status_code == 404:
        return ToolResult("domain_whois", "ok", "verified", f"No RDAP registration record found for {domain}.",
                          [{"description": f"No registration record for {domain}", "weight": 0.20}], {"domain": domain})
    if r.status_code != 200:
        return _unavailable("domain_whois", f"RDAP returned HTTP {r.status_code}")
    reg = next((e.get("eventDate") for e in r.json().get("events", []) if e.get("eventAction") == "registration"), None)
    if not reg:
        return _unavailable("domain_whois", "registration date not present in RDAP response")
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(reg.replace("Z", "+00:00"))).days
    fs = [{"description": f"Domain registered only {age} days ago", "weight": 0.35 if age < 30 else 0.15}] if age < 180 else []
    return ToolResult("domain_whois", "ok", "verified", f"{domain} registered {reg[:10]} ({age} days old, source: RDAP).", fs,
                      {"domain": domain, "age_days": age})


@timed
def safe_browsing(url: str, **_) -> ToolResult:
    key = get_settings().safe_browsing_api_key
    if not key:
        return _unavailable("safe_browsing", "SAFE_BROWSING_API_KEY not configured")
    body = {"client": {"clientId": "kavach", "clientVersion": "0.1"},
            "threatInfo": {"threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"], "platformTypes": ["ANY_PLATFORM"],
                           "threatEntryTypes": ["URL"], "threatEntries": [{"url": url}]}}
    try:
        r = httpx.post(f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}", json=body, timeout=TIMEOUT)
        r.raise_for_status()
    except httpx.HTTPError:
        return _unavailable("safe_browsing", "Safe Browsing request failed")
    matches = r.json().get("matches", [])
    if matches:
        kinds = sorted({m.get("threatType", "?") for m in matches})
        return ToolResult("safe_browsing", "ok", "verified", f"Google Safe Browsing flags this URL: {', '.join(kinds)}.",
                          [{"description": f"Flagged by Google Safe Browsing ({', '.join(kinds)})", "weight": 0.85}], {"matches": kinds})
    return ToolResult("safe_browsing", "ok", "verified", "Not on Google Safe Browsing lists (this does not prove it is safe).", [], {"matches": []})


@timed
def virustotal(url: str, **_) -> ToolResult:
    key = get_settings().virustotal_api_key
    if not key:
        return _unavailable("virustotal", "VIRUSTOTAL_API_KEY not configured")
    uid = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    try:
        r = httpx.get(f"https://www.virustotal.com/api/v3/urls/{uid}", headers={"x-apikey": key}, timeout=TIMEOUT)
    except httpx.HTTPError:
        return _unavailable("virustotal", "VirusTotal request failed")
    if r.status_code == 404:
        return ToolResult("virustotal", "ok", "verified", "VirusTotal has no prior analysis of this URL.", [], {})
    if r.status_code != 200:
        return _unavailable("virustotal", f"VirusTotal returned HTTP {r.status_code}")
    st = r.json()["data"]["attributes"]["last_analysis_stats"]
    bad = st.get("malicious", 0) + st.get("suspicious", 0)
    fs = [{"description": f"{bad} security vendors flag this URL on VirusTotal", "weight": min(0.9, 0.3 + 0.1 * bad)}] if bad else []
    return ToolResult("virustotal", "ok", "verified", f"VirusTotal: {bad} of {sum(st.values())} engines flag the URL.", fs, {"stats": st})


@timed
def cross_case_correlation(entities: list[str], db=None, user_id: str = "", **_) -> ToolResult:
    """Counts OTHER Kavach cases (any user) that mention the same UPI ID/domain. Counts only - no content is revealed."""
    if db is None or not entities:
        return _unavailable("cross_case_correlation", "no entities to correlate")
    from sqlalchemy import func, select
    from app.models.orm import ScamCase
    fs, data = [], {}
    for e in entities[:8]:
        n = db.scalar(select(func.count()).select_from(ScamCase).where(
            ScamCase.redacted_input.ilike(f"%{e}%"), ScamCase.risk_level != "SAFE")) or 0
        data[e] = n
        if n:
            fs.append({"description": f"'{e}' appeared in {n} earlier flagged Kavach case(s)", "weight": min(0.5, 0.2 + 0.1 * n)})
    return ToolResult("cross_case_correlation", "ok", "verified", "Compared against previously flagged Kavach cases (local database).", fs, data)
