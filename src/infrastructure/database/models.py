"""SQLAlchemy 2.0 async ORM models for Financial Access Intelligence Layer."""
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Column,
        DateTime,
        Enum,
        Float,
        ForeignKey,
        Index,
        Integer,
        Numeric,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy.ext.asyncio import AsyncAttrs
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

    class Base(AsyncAttrs, DeclarativeBase):
        """Declarative base for all ORM models."""
        pass

    class FinancialProfileORM(Base):
        """Persisted FinancialProfile aggregate root."""
        __tablename__ = "financial_profiles"

        profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        wallet_url: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
        currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
        status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
        consent_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                       default=lambda: datetime.now(UTC))
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                       default=lambda: datetime.now(UTC),
                                                       onupdate=lambda: datetime.now(UTC))

        # Relationships
        scores: Mapped[list["FAIScoreORM"]] = relationship("FAIScoreORM", back_populates="profile",
                                                            cascade="all, delete-orphan")
        barriers: Mapped[list["BarrierORM"]] = relationship("BarrierORM", back_populates="profile",
                                                              cascade="all, delete-orphan")

        __table_args__ = (Index("ix_profile_wallet", "wallet_url"),)

    class FAIScoreORM(Base):
        """Persisted FAI score snapshot."""
        __tablename__ = "fai_scores"

        score_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("financial_profiles.profile_id"),
                                                   nullable=False, index=True)
        overall_score: Mapped[float] = mapped_column(Float, nullable=False)
        dimension_scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
        methodology: Mapped[str] = mapped_column(String(64), nullable=False, default="DETERMINISTIC_RULES")
        scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v0.1")
        calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                          default=lambda: datetime.now(UTC))

        # Relationship back-reference
        profile: Mapped["FinancialProfileORM"] = relationship("FinancialProfileORM", back_populates="scores")

        __table_args__ = (
            Index("ix_fai_score_profile_calc", "profile_id", "calculated_at"),
        )

    class BarrierORM(Base):
        """Persisted structural barrier diagnosis."""
        __tablename__ = "barriers"

        barrier_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("financial_profiles.profile_id"),
                                                   nullable=False, index=True)
        snapshot_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        barrier_code: Mapped[str] = mapped_column(String(64), nullable=False)
        dimension: Mapped[str] = mapped_column(String(64), nullable=False)
        severity: Mapped[str] = mapped_column(String(32), nullable=False)
        state: Mapped[str] = mapped_column(String(32), nullable=False, default="DIAGNOSED")
        evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
        diagnosed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                         default=lambda: datetime.now(UTC))
        resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

        profile: Mapped["FinancialProfileORM"] = relationship("FinancialProfileORM", back_populates="barriers")

    class InterventionORM(Base):
        """Persisted intervention record."""
        __tablename__ = "interventions"

        intervention_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        barrier_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
        profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
        intervention_type: Mapped[str] = mapped_column(String(64), nullable=False)
        status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
        metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                       default=lambda: datetime.now(UTC))
        executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

        __table_args__ = (
            Index("ix_intervention_profile", "profile_id"),
            Index("ix_intervention_barrier", "barrier_id"),
        )

    class PaymentAuditLogORM(Base):
        """Immutable Open Payments execution audit trail."""
        __tablename__ = "payment_audit_log"

        log_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        intervention_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
        profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
        sender_wallet: Mapped[str] = mapped_column(String(512), nullable=False)
        receiver_wallet: Mapped[str] = mapped_column(String(512), nullable=False)
        asset_code: Mapped[str] = mapped_column(String(10), nullable=False)
        debit_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
        estimated_fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=Decimal("0"))
        outgoing_payment_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
        status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
        executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                        default=lambda: datetime.now(UTC))

        __table_args__ = (
            Index("ix_payment_log_profile", "profile_id"),
        )

except ImportError:
    # SQLAlchemy not installed — graceful fallback for bare Python environments
    Base = object  # type: ignore
    FinancialProfileORM = None  # type: ignore
    FAIScoreORM = None  # type: ignore
    BarrierORM = None  # type: ignore
    InterventionORM = None  # type: ignore
    PaymentAuditLogORM = None  # type: ignore
