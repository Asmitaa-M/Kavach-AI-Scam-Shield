"""Case creation, evidence persistence and guardian-alert generation."""
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.orm import Evidence, Guardian, GuardianAlert, ScamCase, User
from app.security.redact import redact


def next_case_id(db: Session) -> str:
    n = (db.scalar(select(func.count()).select_from(ScamCase)) or 0) + 1
    return f"KAV-{datetime.now(timezone.utc).year}-{n:04d}"


def create_case(db: Session, user: User, input_type: str, score: int, level: str, summary: str,
                raw_text: str, evidence: list[dict], simulated: bool = False) -> ScamCase:
    case = ScamCase(case_id=next_case_id(db), user_id=user.user_id, input_type=input_type, risk_score=score,
                    risk_level=level, summary=summary[:500], redacted_input=redact(raw_text)[:2000],
                    is_simulated=simulated)
    for e in evidence:
        case.evidence.append(Evidence(evidence_type=e.get("type", "indicator"), description=e["description"][:500],
                                      source=e.get("source", "kavach-tier1"), confidence=float(e.get("confidence", 0)),
                                      provenance=e.get("provenance", "heuristic")))
    db.add(case)
    db.flush()
    if level == "HIGH RISK":
        raise_alerts(db, user, case)
    db.commit()
    return case


def raise_alerts(db: Session, user: User, case: ScamCase) -> int:
    """In-app alerts only. No SMS/WhatsApp is sent - no provider is configured."""
    guardians = db.scalars(select(Guardian).where(Guardian.owner_id == user.user_id, Guardian.status == "active")).all()
    for g in guardians:
        db.add(GuardianAlert(case_id=case.case_id, guardian_id=g.guardian_id, recipient_user_id=g.guardian_user_id,
                             incident_type=case.input_type, risk_score=case.risk_score,
                             summary=f"{user.name} may be targeted by a {case.input_type} scam. {case.summary}"[:400]))
    return len(guardians)
