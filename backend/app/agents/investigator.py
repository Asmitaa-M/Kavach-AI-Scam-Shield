"""Agentic investigator: LangGraph state machine with an ADAPTIVE tool loop.

classify -> plan -> act (loop: pop tool, run, tools may enqueue follow-ups) -> fuse -> report.
The verdict is computed from evidence by code. The LLM (optional) only writes the explanation."""
import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.tools import security_tools as T
from app.security.injection import detect_injection
from app.services import gemini
from app.services.tier1.scoring import level_for, recommendations_for, analyze_text

_URL = re.compile(r"(?i)\b((?:https?://|www\.)[^\s<>\"')]+|(?:[a-z0-9\-]+\.)+(?:com|in|net|org|xyz|top|click|link|info|online|site|cc|ly|buzz|icu)(?:/[^\s<>\"')]*)?)")
TOOLS = {"suspicious_language": T.suspicious_language, "upi_id_analyzer": T.upi_id_analyzer,
         "url_lexical_check": T.url_lexical_check, "domain_whois": T.domain_whois, "safe_browsing": T.safe_browsing,
         "virustotal": T.virustotal, "cross_case_correlation": T.cross_case_correlation}


class State(TypedDict, total=False):
    text: str; kind: str; db: Any; user_id: str; language: str
    scam_type: str; plan: list[str]; queue: list[tuple[str, dict]]; steps: list[dict]; results: list[T.ToolResult]
    urls: list[str]; entities: list[str]; report: dict


def classify(s: State) -> State:
    t = s["text"]; low = t.lower()
    urls = [u.rstrip(".,;)") for u in dict.fromkeys(m.group(1) for m in _URL.finditer(t)) if "@" not in u]
    has_upi = bool(re.search(r"[\w.\-]{2,}@[a-z]{2,}\b", t, re.I)) or s.get("kind") == "upi" or bool(re.search(r"\b(upi|collect request|gpay|phonepe|paytm)\b", low))
    if has_upi: st = "UPI payment scam"
    elif re.search(r"\b(otp|kyc|bank|account)\b", low) and urls: st = "Phishing / fake bank link"
    elif re.search(r"(accident|arrest|hospital|trouble|papa|amma|appa|magan|beta)", low): st = "Family impersonation"
    elif urls: st = "Suspicious link"
    else: st = "General social-engineering message"
    return {"scam_type": st, "urls": urls, "steps": [], "results": []}


def plan(s: State) -> State:
    q: list[tuple[str, dict]] = [("suspicious_language", {})]
    if s["scam_type"] == "UPI payment scam" or re.search(r"[\w.\-]{2,}@[a-z]{2,}\b", s["text"], re.I):
        q.append(("upi_id_analyzer", {}))
    for u in s["urls"][:3]:
        q.append(("url_lexical_check", {"url": u}))
    return {"queue": q, "plan": [n for n, _ in q]}


def act(s: State) -> State:
    queue = list(s["queue"]); name, args = queue.pop(0)
    kwargs = {"text": s["text"], "kind": "upi" if s["scam_type"] == "UPI payment scam" else "call", **args}
    r = TOOLS[name](**kwargs)
    # adaptive follow-ups proposed by the tool (e.g. a URL was found -> check WHOIS / SafeBrowsing / VirusTotal)
    done = {x["tool"] + str(x.get("arg", "")) for x in s["steps"]}
    for fname, fargs in r.followups:
        if fname + str(fargs.get("url", "")) not in done and (fname, fargs) not in queue:
            queue.append((fname, fargs))
    # once identifiers are known, correlate against previous cases (once)
    entities = list(s.get("entities", []))
    if name == "upi_id_analyzer": entities += r.data.get("upi_ids", [])
    if name == "url_lexical_check": entities.append(r.data.get("host", ""))
    if not queue and entities and not any(x["tool"] == "cross_case_correlation" for x in s["steps"] + [{"tool": name}]):
        queue.append(("cross_case_correlation", {"entities": [e for e in dict.fromkeys(entities) if e], "db": s.get("db"), "user_id": s.get("user_id", "")}))
    step = {"tool": name, "arg": args.get("url", ""), "status": r.status, "provenance": r.provenance, "summary": r.summary, "ms": r.ms}
    return {"queue": queue, "steps": s["steps"] + [step], "results": s["results"] + [r], "entities": entities}


def more(s: State) -> str:
    return "act" if s["queue"] and len(s["steps"]) < 14 else "fuse"


def fuse(s: State) -> State:
    surv, evidence = 1.0, []
    inj = detect_injection(s["text"])
    for r in s["results"]:
        if r.tool == "suspicious_language":
            base = r.data.get("score", 0) / 100.0
            surv *= 1.0 - base
            for f in r.findings:
                evidence.append({"type": "indicator", "description": f["description"], "source": r.tool, "confidence": f["weight"], "provenance": "heuristic"})
            continue
        for f in r.findings:
            surv *= 1.0 - f["weight"]
            evidence.append({"type": "indicator", "description": f["description"], "source": r.tool, "confidence": f["weight"], "provenance": r.provenance})
        if r.status != "ok":
            evidence.append({"type": "unavailable_check", "description": f"{r.tool}: {r.summary}", "source": r.tool, "confidence": 0.0, "provenance": "unavailable"})
    if inj:
        surv *= 0.5
        evidence.append({"type": "indicator", "description": "Text contains instructions aimed at the analysis system (manipulation attempt) - ignored", "source": "injection_guard", "confidence": 0.5, "provenance": "heuristic"})
    score = int(round((1.0 - surv) * 100))
    verified_bad = any(e["provenance"] == "verified" and e["confidence"] >= 0.8 for e in evidence)
    if verified_bad: score = max(score, 90)
    return {"report": {"score": score, "level": level_for(score), "evidence": evidence}}


def report(s: State) -> State:
    rep = s["report"]; t1 = analyze_text(s["text"], "upi" if s["scam_type"] == "UPI payment scam" else "call")
    recs = recommendations_for(t1)
    if rep["level"] != "SAFE" and rep["level"] != t1.level:
        recs = recs or ["Do not act on this message until verified."]
    unavailable = [e["description"] for e in rep["evidence"] if e["provenance"] == "unavailable"]
    expl = gemini.explain(s["text"], rep["level"], [e["description"] for e in rep["evidence"]], s.get("language", "en"))
    rep.update({"scam_type": s["scam_type"], "plan_initial": s["plan"], "steps": s["steps"], "recommendations": recs,
                "unavailable_checks": unavailable,
                "llm_explanation": expl.model_dump() if expl else None,
                "llm_status": "used" if expl else "not used (no key configured or request failed)",
                "verified": [e for e in rep["evidence"] if e["provenance"] == "verified"],
                "heuristic": [e for e in rep["evidence"] if e["provenance"] == "heuristic"],
                "disclaimer": "Heuristic findings are indicators, not proof. Unavailable checks were NOT performed."})
    return {"report": rep}


def build_graph():
    g = StateGraph(State)
    for n, f in [("classify", classify), ("make_plan", plan), ("act", act), ("fuse", fuse), ("write_report", report)]:
        g.add_node(n, f)
    g.set_entry_point("classify"); g.add_edge("classify", "make_plan"); g.add_edge("make_plan", "act")
    g.add_conditional_edges("act", more, {"act": "act", "fuse": "fuse"}); g.add_edge("fuse", "write_report"); g.add_edge("write_report", END)
    return g.compile()


_graph = None

def investigate(text: str, kind: str = "auto", db=None, user_id: str = "", language: str = "en") -> dict:
    global _graph
    _graph = _graph or build_graph()
    out = _graph.invoke({"text": text[:6000], "kind": kind, "db": db, "user_id": user_id, "language": language})
    return out["report"]
