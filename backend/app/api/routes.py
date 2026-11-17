import logging
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, rate_limited
from app.database.db import get_db
from app.models.orm import (FamilyContact, Guardian, GuardianAlert, ScamCase, User, VerificationAttempt)
from app.security.hashing import create_token, hash_password, hash_phrase, verify_password, verify_phrase
from app.security.uploads import read_validated
from app.services import cases as case_svc
from app.services.ocr import extract_text
from app.services.tier1 import analyze_text, recommendations_for

log = logging.getLogger("kavach")
router = APIRouter(dependencies=[Depends(rate_limited)])

# ---------- auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferred_language: Literal["en", "ta", "hi"] = "en"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

def _user_out(u: User) -> dict:
    return {"user_id": u.user_id, "name": u.name, "email": u.email, "preferred_language": u.preferred_language}

@router.post("/auth/register", status_code=201, tags=["auth"])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    u = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password),
             preferred_language=body.preferred_language)
    db.add(u)
    # Link any guardian invitations that were addressed to this email.
    db.flush()
    for g in db.scalars(select(Guardian).where(func.lower(Guardian.email) == email)).all():
        g.guardian_user_id = u.user_id
    db.commit()
    return {"token": create_token(u.user_id), "user": _user_out(u)}

@router.post("/auth/login", tags=["auth"])
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == body.email.lower()))
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")  # same message either way
    return {"token": create_token(u.user_id), "user": _user_out(u)}

@router.get("/auth/me", tags=["auth"])
def me(user: User = Depends(current_user)):
    return _user_out(user)

class LangIn(BaseModel):
    preferred_language: Literal["en", "ta", "hi"]

@router.patch("/auth/language", tags=["auth"])
def set_language(body: LangIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.preferred_language = body.preferred_language
    db.commit()
    return _user_out(user)

# ---------- analysis ----------
class TextIn(BaseModel):
    text: str = Field(min_length=3, max_length=6000)
    is_demo_sample: bool = False

def _result_payload(case: ScamCase, res, extra: dict | None = None) -> dict:
    return {"case_id": case.case_id, "score": res.score, "level": res.level,
            "indicators": [i.__dict__ for i in res.indicators], "tactics": res.tactics,
            "ml_prob": res.ml_prob, "notes": res.notes, "upi": res.upi,
            "recommendations": recommendations_for(res),
            "guardians_alerted": res.level == "HIGH RISK",
            "disclaimer": "Kavach cannot block or reverse payments. It helps you verify before you act.",
            **(extra or {})}

def _summary(res) -> str:
    labels = [i.label for i in res.indicators[:3]]
    return "; ".join(labels) if labels else "No scam tactics detected."

def _run(kind: str, text: str, user: User, db: Session, simulated: bool, extra: dict | None = None):
    res = analyze_text(text, kind)
    ev = [{"type": i.id, "description": i.label + (f" ('{i.matched[:60]}')" if i.matched else ""),
           "source": "kavach-tier1", "confidence": i.weight, "provenance": i.provenance} for i in res.indicators]
    case = case_svc.create_case(db, user, kind, res.score, res.level, _summary(res), text, ev, simulated)
    log.info("case=%s kind=%s level=%s", case.case_id, kind, res.level)  # never log raw text
    return _result_payload(case, res, extra)

@router.post("/analyze/upi", tags=["analysis"])
def analyze_upi(body: TextIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _run("upi", body.text, user, db, body.is_demo_sample)

@router.post("/analyze/upi/screenshot", tags=["analysis"])
async def analyze_upi_screenshot(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = await read_validated(file, "image")
    try:
        text, langs = extract_text(data)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if len(text) < 5:
        raise HTTPException(422, "No readable text found in the screenshot. Try a clearer image.")
    return _run("upi", text, user, db, False, {"ocr_text": text[:3000], "ocr_languages": langs})

@router.post("/analyze/call", tags=["analysis"])
def analyze_call(body: TextIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _run("call", body.text, user, db, body.is_demo_sample)

@router.post("/analyze/call/audio", tags=["analysis"])
async def analyze_call_audio(file: UploadFile = File(...), user: User = Depends(current_user)):
    await read_validated(file, "audio")
    # Honest status: no speech-to-text engine is bundled in this build.
    raise HTTPException(501, "Audio transcription is not configured on this server. Paste the transcript instead "
                             "(speech-to-text is on the roadmap). No audio was stored.")

# ---------- family safe words ----------
class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    relationship_label: str = Field(default="family", max_length=60)
    phrase: str = Field(min_length=4, max_length=80)

class VerifyIn(BaseModel):
    phrase: str = Field(min_length=1, max_length=80)
    notify_guardians: bool = True

def _contact_out(c: FamilyContact) -> dict:  # never includes the hash or phrase
    return {"contact_id": c.contact_id, "name": c.name, "relationship_label": c.relationship_label,
            "created_at": c.created_at, "locked": bool(c.locked_until and c.locked_until > datetime.now(timezone.utc))}

@router.get("/family/contacts", tags=["safe-word"])
def list_contacts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [_contact_out(c) for c in db.scalars(select(FamilyContact).where(FamilyContact.owner_id == user.user_id))]

@router.post("/family/contacts", status_code=201, tags=["safe-word"])
def add_contact(body: ContactIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = FamilyContact(owner_id=user.user_id, name=body.name.strip(), relationship_label=body.relationship_label.strip(),
                      hashed_secret=hash_phrase(body.phrase))
    db.add(c); db.commit()
    return _contact_out(c)

@router.delete("/family/contacts/{contact_id}", status_code=204, tags=["safe-word"])
def delete_contact(contact_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(FamilyContact, contact_id)
    if not c or c.owner_id != user.user_id:
        raise HTTPException(404, "Contact not found")
    for a in db.scalars(select(VerificationAttempt).where(VerificationAttempt.contact_id == contact_id)):
        db.delete(a)
    db.delete(c); db.commit()

MAX_FAILS, LOCK_MIN = 5, 15

@router.post("/family/contacts/{contact_id}/verify", tags=["safe-word"])
def verify_contact(contact_id: str, body: VerifyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(FamilyContact, contact_id)
    if not c or c.owner_id != user.user_id:
        raise HTTPException(404, "Contact not found")
    now = datetime.now(timezone.utc)
    if c.locked_until and c.locked_until.replace(tzinfo=timezone.utc) > now:
        db.add(VerificationAttempt(contact_id=c.contact_id, outcome="locked")); db.commit()
        raise HTTPException(429, "Too many failed attempts. Try again later and call the family member directly.")
    ok = verify_phrase(body.phrase, c.hashed_secret)
    db.add(VerificationAttempt(contact_id=c.contact_id, outcome="verified" if ok else "failed"))
    caveat = "A safe word is one extra check, not absolute proof of identity."
    if ok:
        c.failed_attempts = 0; db.commit()
        return {"status": "VERIFIED", "message": f"The phrase matches for {c.name}.", "caveat": caveat}
    c.failed_attempts += 1
    if c.failed_attempts >= MAX_FAILS:
        c.locked_until = now + timedelta(minutes=LOCK_MIN); c.failed_attempts = 0
    alerted = 0
    if body.notify_guardians:
        case = case_svc.create_case(db, user, "call", 85, "HIGH RISK",
                                    f"Caller claiming to be {c.name} failed the family safe-word check.",
                                    "safe-word verification failed",
                                    [{"type": "safeword_failed", "description": f"Caller could not give the safe word for {c.name}",
                                      "source": "safe-word", "confidence": 0.85, "provenance": "verified"}])
        alerted = db.scalar(select(func.count()).select_from(GuardianAlert).where(GuardianAlert.case_id == case.case_id)) or 0
    else:
        db.commit()
    return {"status": "VERIFICATION FAILED", "message": f"The phrase does not match for {c.name}.", "caveat": caveat,
            "next_steps": [f"Hang up. Call {c.name} on the number saved in your phone.",
                           "Do not send money or share OTP/PIN.", "Tell another family member.",
                           "If money was sent, call 1930."], "guardians_alerted": alerted}

# ---------- guardians + alerts ----------
class GuardianIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr

@router.get("/guardians", tags=["guardians"])
def list_guardians(user: User = Depends(current_user), db: Session = Depends(get_db)):
    gs = db.scalars(select(Guardian).where(Guardian.owner_id == user.user_id, Guardian.status == "active")).all()
    return [{"guardian_id": g.guardian_id, "name": g.name, "email": g.email, "linked_account": g.guardian_user_id is not None} for g in gs]

@router.post("/guardians", status_code=201, tags=["guardians"])
def add_guardian(body: GuardianIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    email = body.email.lower()
    if email == user.email:
        raise HTTPException(400, "You cannot be your own guardian")
    if db.scalar(select(Guardian).where(Guardian.owner_id == user.user_id, Guardian.email == email, Guardian.status == "active")):
        raise HTTPException(409, "Guardian already added")
    linked = db.scalar(select(User).where(User.email == email))
    g = Guardian(owner_id=user.user_id, name=body.name.strip(), email=email, guardian_user_id=linked.user_id if linked else None)
    db.add(g); db.commit()
    return {"guardian_id": g.guardian_id, "name": g.name, "email": g.email, "linked_account": linked is not None}

@router.delete("/guardians/{gid}", status_code=204, tags=["guardians"])
def remove_guardian(gid: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    g = db.get(Guardian, gid)
    if not g or g.owner_id != user.user_id:
        raise HTTPException(404, "Guardian not found")
    g.status = "revoked"; db.commit()

def _alert_out(a: GuardianAlert) -> dict:
    return {"alert_id": a.alert_id, "case_id": a.case_id, "incident_type": a.incident_type, "risk_score": a.risk_score,
            "summary": a.summary, "status": a.notification_status, "delivery": a.delivery, "created_at": a.created_at}

@router.get("/alerts", tags=["alerts"])
def my_alerts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Alerts where I am the guardian (received)."""
    rows = db.scalars(select(GuardianAlert).where(GuardianAlert.recipient_user_id == user.user_id).order_by(GuardianAlert.created_at.desc()).limit(100))
    return [_alert_out(a) for a in rows]

@router.get("/alerts/sent", tags=["alerts"])
def sent_alerts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Alerts generated about my incidents, with the guardian each went to."""
    q = (select(GuardianAlert, Guardian.name).join(Guardian, Guardian.guardian_id == GuardianAlert.guardian_id)
         .where(Guardian.owner_id == user.user_id).order_by(GuardianAlert.created_at.desc()).limit(100))
    return [{**_alert_out(a), "guardian_name": n} for a, n in db.execute(q)]

@router.post("/alerts/{alert_id}/read", tags=["alerts"])
def mark_read(alert_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = db.get(GuardianAlert, alert_id)
    if not a or a.recipient_user_id != user.user_id:
        raise HTTPException(404, "Alert not found")
    a.notification_status = "read"; db.commit()
    return _alert_out(a)

# ---------- history + dashboard ----------
def _case_out(c: ScamCase, with_evidence: bool = False) -> dict:
    d = {"case_id": c.case_id, "input_type": c.input_type, "risk_score": c.risk_score, "risk_level": c.risk_level,
         "summary": c.summary, "status": c.status, "is_simulated": c.is_simulated, "created_at": c.created_at}
    if with_evidence:
        d["redacted_input"] = c.redacted_input
        d["evidence"] = [{"type": e.evidence_type, "description": e.description, "source": e.source,
                          "confidence": e.confidence, "provenance": e.provenance} for e in c.evidence]
    return d

@router.get("/cases", tags=["cases"])
def list_cases(limit: int = 50, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(ScamCase).where(ScamCase.user_id == user.user_id).order_by(ScamCase.created_at.desc()).limit(min(limit, 200)))
    return [_case_out(c) for c in rows]

@router.get("/cases/{case_id}", tags=["cases"])
def get_case(case_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(ScamCase, case_id)
    if not c or c.user_id != user.user_id:
        raise HTTPException(404, "Case not found")
    return _case_out(c, True)

@router.get("/dashboard/stats", tags=["cases"])
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    cs = db.scalars(select(ScamCase).where(ScamCase.user_id == user.user_id).order_by(ScamCase.created_at.desc())).all()
    dist = {"SAFE": 0, "SUSPICIOUS": 0, "HIGH RISK": 0}
    for c in cs:
        dist[c.risk_level] = dist.get(c.risk_level, 0) + 1
    unread = db.scalar(select(func.count()).select_from(GuardianAlert).where(
        GuardianAlert.recipient_user_id == user.user_id, GuardianAlert.notification_status == "unread")) or 0
    return {"total_scans": len(cs), "high_risk": dist["HIGH RISK"], "safe": dist["SAFE"], "distribution": dist,
            "unread_alerts": unread, "recent": [_case_out(c) for c in cs[:6]]}

# ---------- agentic investigation ----------
from app.agents.investigator import investigate as run_investigation  # noqa: E402

class InvestigateIn(BaseModel):
    text: str = Field(min_length=3, max_length=6000)
    is_demo_sample: bool = False

@router.post("/investigate", tags=["agent"])
def investigate_endpoint(body: InvestigateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rep = run_investigation(body.text, "auto", db, user.user_id, user.preferred_language)
    ev = [e for e in rep["evidence"]]
    case = case_svc.create_case(db, user, "investigation", rep["score"], rep["level"],
                                f"{rep['scam_type']}: " + "; ".join(e["description"] for e in ev[:2])[:300], body.text, ev, body.is_demo_sample)
    return {"case_id": case.case_id, **{k: v for k, v in rep.items() if k != "evidence"}, "evidence": ev, "guardians_alerted": rep["level"] == "HIGH RISK"}
