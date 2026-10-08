from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class DisputeCase(Base):
    __tablename__ = "dispute_cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    chip: Mapped[str] = mapped_column(String(64))
    complaint: Mapped[str] = mapped_column(Text)

    # Decision produced by the engine for this case
    dispute_type: Mapped[str] = mapped_column(String(128))
    decision: Mapped[str] = mapped_column(String(128))
    decision_class: Mapped[str] = mapped_column(String(16))  # green | orange | red
    risk: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[int] = mapped_column(Integer)
    reasoning: Mapped[str] = mapped_column(Text)
    actions: Mapped[list[str]] = mapped_column(JSON)
    letter: Mapped[str] = mapped_column(Text)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="Transaction.id"
    )
    audit_entries: Mapped[list["AuditEntry"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("dispute_cases.id", ondelete="CASCADE"))
    merchant: Mapped[str] = mapped_column(String(128))
    amount: Mapped[str] = mapped_column(String(32))
    date: Mapped[str] = mapped_column(String(32))
    auth: Mapped[str] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(32))

    case: Mapped[DisputeCase] = relationship(back_populates="transactions")


class AuditEntry(Base):
    """One row per engine run: who ran it, when, and what was decided."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("dispute_cases.id", ondelete="CASCADE"))
    operator_id: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(128))
    confidence: Mapped[int] = mapped_column(Integer)
    reasoning: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    case: Mapped[DisputeCase] = relationship(back_populates="audit_entries")
