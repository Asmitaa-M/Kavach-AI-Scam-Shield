import uuid
from datetime import datetime, timezone
from sqlalchemy import (Boolean, DateTime, Float, ForeignKey, Integer, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base


def _id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Guardian(Base):
    """A trusted person linked to a user. May be a registered user or just a contact."""
    __tablename__ = "guardians"
    __table_args__ = (UniqueConstraint("owner_id", "email"),)
    guardian_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    guardian_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|revoked
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class FamilyContact(Base):
    """Family member + hashed verification phrase. The phrase itself is never stored."""
    __tablename__ = "family_contacts"
    contact_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    relationship_label: Mapped[str] = mapped_column(String(60), default="family")
    hashed_secret: Mapped[str] = mapped_column(String(255))
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class VerificationAttempt(Base):
    """Outcome log only - never the submitted phrase."""
    __tablename__ = "verification_attempts"
    attempt_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    contact_id: Mapped[str] = mapped_column(ForeignKey("family_contacts.contact_id"), index=True)
    outcome: Mapped[str] = mapped_column(String(16))  # verified|failed|locked
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ScamCase(Base):
    __tablename__ = "scam_cases"
    case_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    input_type: Mapped[str] = mapped_column(String(16))  # upi|call|investigation
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(16))  # SAFE|SUSPICIOUS|HIGH RISK
    summary: Mapped[str] = mapped_column(Text, default="")
    redacted_input: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="open")
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    evidence: Mapped[list["Evidence"]] = relationship(cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"
    evidence_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("scam_cases.case_id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(60))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    provenance: Mapped[str] = mapped_column(String(16), default="heuristic")  # verified|heuristic|unavailable


class GuardianAlert(Base):
    __tablename__ = "guardian_alerts"
    alert_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("scam_cases.case_id"), index=True)
    guardian_id: Mapped[str] = mapped_column(ForeignKey("guardians.guardian_id"), index=True)
    recipient_user_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    incident_type: Mapped[str] = mapped_column(String(24))
    risk_score: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)
    notification_status: Mapped[str] = mapped_column(String(16), default="unread")  # unread|read
    delivery: Mapped[str] = mapped_column(String(24), default="in_app")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
