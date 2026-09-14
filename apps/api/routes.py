"""FastAPI API Routes for Financial Access Intelligence Layer with Strict Dependency Injection."""
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.application.access_index.use_cases import (
    CalculateFAIScoreUseCase,
    ExportAuditReportUseCase,
)
from src.application.common.dto import CalculateFAIScoreRequestDTO
from src.application.interventions.use_cases import RecommendInterventionsUseCase
from src.application.payments.use_cases import (
    ExecuteInterventionPaymentUseCase,
    OptimizeRouteUseCase,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency Provider Factories for FastAPI DI
# ---------------------------------------------------------------------------


def get_calculate_fai_score_use_case() -> CalculateFAIScoreUseCase:
    return CalculateFAIScoreUseCase()


def get_recommend_interventions_use_case() -> RecommendInterventionsUseCase:
    return RecommendInterventionsUseCase()


def get_execute_intervention_payment_use_case() -> ExecuteInterventionPaymentUseCase:
    return ExecuteInterventionPaymentUseCase()


def get_optimize_route_use_case() -> OptimizeRouteUseCase:
    return OptimizeRouteUseCase()


def get_export_audit_report_use_case() -> ExportAuditReportUseCase:
    return ExportAuditReportUseCase()


def _resolve_dep(dep_arg: Any, factory: Any) -> Any:
    """Resolves dependency if invoked directly in unit tests without FastAPI DI context."""
    if dep_arg is None or hasattr(dep_arg, "dependency"):
        return factory()
    return dep_arg


# ---------------------------------------------------------------------------
# Base Schema Configuration
# ---------------------------------------------------------------------------


class StrictSchema(BaseModel):
    """Base Pydantic v2 Schema with dict subscription support for testing compatibility."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __contains__(self, key: object) -> bool:
        return hasattr(self, str(key))

    def __iter__(self) -> Any:
        return iter(self.model_dump())


# ---------------------------------------------------------------------------
# Input Schemas (DTOs)
# ---------------------------------------------------------------------------


class FeatureIngestionRequest(StrictSchema):
    profile_id: UUID
    wallet_count: int = Field(default=1, ge=0)
    ilp_reachable: bool = True
    tx_success_rate: float = Field(default=0.95, ge=0.0, le=1.0)
    avg_connection_latency_ms: float = Field(default=250.0, ge=0.0)
    fee_to_volume_ratio: float = Field(default=0.01, ge=0.0)
    settlement_fulfillment_rate: float = Field(default=0.98, ge=0.0, le=1.0)
    cross_asset_success_rate: float = Field(default=0.90, ge=0.0, le=1.0)
    tx_frequency_monthly: int = Field(default=12, ge=0)
    tx_volume_monthly_usd: float = Field(default=250.0, ge=0.0)
    reserve_liquidity_usd: float = Field(default=50.0, ge=0.0)
    fallback_route_available: bool = True
    methodology: Literal[
        "DETERMINISTIC_RULES",
        "STATISTICAL_COHORT",
        "ML_XGBOOST",
        "NON_LINEAR_MCDA",
    ] = "DETERMINISTIC_RULES"


# Alias for backward compatibility with unit tests
FeatureIngestionSchema = FeatureIngestionRequest


class BarrierRequest(StrictSchema):
    barrier_id: UUID = Field(default_factory=uuid4)
    profile_id: UUID = Field(default_factory=uuid4)
    barrier_code: str = Field(min_length=1, max_length=64)
    dimension: str = Field(min_length=1, max_length=64)
    severity: str = Field(min_length=1, max_length=32)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExecutePaymentRequest(StrictSchema):
    intervention_id: UUID
    sender_wallet: str = Field(min_length=1, max_length=512)
    receiver_wallet: str = Field(min_length=1, max_length=512)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=20, decimal_places=8)
    asset_code: str = Field(default="USD", min_length=3, max_length=10)
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))

    @field_validator("amount", mode="before")
    @classmethod
    def convert_amount_to_decimal(cls, value: object) -> object:
        if isinstance(value, (float, int, str)):
            return Decimal(str(value))
        return value


# Alias for backward compatibility with unit tests
ExecuteInterventionRequestSchema = ExecutePaymentRequest


class RouteOptimizationRequest(StrictSchema):
    source_asset: str = Field(default="USD", min_length=3, max_length=10)
    destination_asset: str = Field(default="EUR", min_length=3, max_length=10)
    amount_usd: Decimal = Field(default=Decimal("100.00"), gt=Decimal("0"), max_digits=20, decimal_places=8)

    @field_validator("amount_usd", mode="before")
    @classmethod
    def convert_amount_usd_to_decimal(cls, value: object) -> object:
        if isinstance(value, (float, int, str)):
            return Decimal(str(value))
        return value


class ReportExportRequest(StrictSchema):
    profile_id: UUID
    fai_score_data: dict[str, Any]
    interventions_executed: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Output Schemas (DTOs)
# ---------------------------------------------------------------------------


class HealthResponse(StrictSchema):
    status: Literal["healthy"]
    service: str


class BarrierResponse(StrictSchema):
    barrier_id: UUID
    barrier_code: str
    dimension: str
    severity: str
    evidence: dict[str, Any]


class FaiScoreResponse(StrictSchema):
    score_id: UUID
    profile_id: UUID
    overall_score: Decimal
    dimension_scores: dict[str, Decimal]
    barriers: list[BarrierResponse]
    scoring_version: str
    methodology: str
    calculated_at: str


class InterventionResponse(StrictSchema):
    intervention_id: UUID
    barrier_id: UUID
    profile_id: UUID
    intervention_type: str
    status: str
    metadata: dict[str, Any]


class InterventionListResponse(StrictSchema):
    interventions_count: int
    interventions: list[InterventionResponse]


class PaymentResponse(StrictSchema):
    status: Literal["SUBMITTED", "COMPLETED", "FAILED", "SUCCESS"]
    intervention_id: UUID
    open_payments_outgoing_id: str
    debit_amount: Decimal
    asset_code: str
    estimated_fee: Decimal


class RouteOptimizationResponse(StrictSchema):
    recommended_route_id: str
    source_asset: str
    destination_asset: str
    predicted_fee_pct: Decimal
    predicted_success_probability: Decimal
    estimated_settlement_ms: Decimal
    liquidity_provider: str
    recommended_action: str


class AuditReportResponse(StrictSchema):
    profile_id: UUID
    overall_score: Decimal
    total_fees_saved_usd: Decimal
    report_markdown: str


# ---------------------------------------------------------------------------
# HTTP Endpoints (Controller Layer < 10 lines per function)
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service="financial-access-intelligence")


@router.post("/api/v1/scores/calculate", response_model=FaiScoreResponse, tags=["FAI Scoring"])
async def calculate_fai_score(
    payload: FeatureIngestionRequest,
    use_case: CalculateFAIScoreUseCase = Depends(get_calculate_fai_score_use_case),
) -> FaiScoreResponse:
    uc = _resolve_dep(use_case, get_calculate_fai_score_use_case)
    dto_req = CalculateFAIScoreRequestDTO(
        profile_id=payload.profile_id,
        wallet_count=payload.wallet_count,
        ilp_reachable=payload.ilp_reachable,
        tx_success_rate=payload.tx_success_rate,
        avg_connection_latency_ms=payload.avg_connection_latency_ms,
        fee_to_volume_ratio=payload.fee_to_volume_ratio,
        settlement_fulfillment_rate=payload.settlement_fulfillment_rate,
        cross_asset_success_rate=payload.cross_asset_success_rate,
        tx_frequency_monthly=payload.tx_frequency_monthly,
        tx_volume_monthly_usd=payload.tx_volume_monthly_usd,
        reserve_liquidity_usd=payload.reserve_liquidity_usd,
        fallback_route_available=payload.fallback_route_available,
        methodology=payload.methodology,
    )
    result = uc.execute(dto_req)
    return FaiScoreResponse(
        score_id=result.score_id,
        profile_id=result.profile_id,
        overall_score=Decimal(str(round(result.overall_score, 2))),
        dimension_scores={k: Decimal(str(round(v, 2))) for k, v in result.dimension_scores.items()},
        barriers=[
            BarrierResponse(
                barrier_id=b.barrier_id,
                barrier_code=b.barrier_code,
                dimension=b.dimension,
                severity=b.severity,
                evidence=b.evidence,
            )
            for b in result.barriers
        ],
        scoring_version=result.scoring_version,
        methodology=result.methodology,
        calculated_at=result.calculated_at,
    )


@router.post("/api/v1/interventions/recommend", response_model=InterventionListResponse, tags=["Interventions"])
async def recommend_interventions(
    payload: list[BarrierRequest],
    use_case: RecommendInterventionsUseCase = Depends(get_recommend_interventions_use_case),
) -> InterventionListResponse:
    uc = _resolve_dep(use_case, get_recommend_interventions_use_case)
    raw_payload = [b.model_dump() for b in payload]
    res = uc.execute(raw_payload)
    return InterventionListResponse(
        interventions_count=res["interventions_count"],
        interventions=[
            InterventionResponse(
                intervention_id=i["intervention_id"],
                barrier_id=i["barrier_id"],
                profile_id=i["profile_id"],
                intervention_type=i["intervention_type"],
                status=i["status"],
                metadata=i["metadata"],
            )
            for i in res["interventions"]
        ],
    )


@router.post("/api/v1/payments/execute", response_model=PaymentResponse, tags=["Open Payments"])
async def execute_intervention_payment(
    payload: ExecutePaymentRequest,
    use_case: ExecuteInterventionPaymentUseCase = Depends(get_execute_intervention_payment_use_case),
) -> PaymentResponse:
    uc = _resolve_dep(use_case, get_execute_intervention_payment_use_case)
    res = await uc.execute(
        intervention_id=payload.intervention_id,
        sender_wallet_str=payload.sender_wallet,
        receiver_wallet_str=payload.receiver_wallet,
        amount=payload.amount,
        asset_code=payload.asset_code,
        idempotency_key=payload.idempotency_key,
    )
    status_val = res["status"]
    if status_val in ("COMPLETED", "SUBMITTED"):
        status_val = "SUCCESS"
    return PaymentResponse(
        status=status_val,
        intervention_id=res["intervention_id"],
        open_payments_outgoing_id=res["open_payments_outgoing_id"],
        debit_amount=res["debit_amount"],
        asset_code=res["asset_code"],
        estimated_fee=res["estimated_fee"],
    )


@router.post("/api/v1/routes/optimize", response_model=RouteOptimizationResponse, tags=["Routing"])
async def optimize_route(
    payload: RouteOptimizationRequest,
    use_case: OptimizeRouteUseCase = Depends(get_optimize_route_use_case),
) -> RouteOptimizationResponse:
    uc = _resolve_dep(use_case, get_optimize_route_use_case)
    res = uc.execute(
        source_asset=payload.source_asset,
        destination_asset=payload.destination_asset,
        amount_usd=payload.amount_usd,
    )
    return RouteOptimizationResponse(**res)


@router.post("/api/v1/reports/export", response_model=AuditReportResponse, tags=["Audit"])
async def export_audit_report(
    payload: ReportExportRequest,
    use_case: ExportAuditReportUseCase = Depends(get_export_audit_report_use_case),
) -> AuditReportResponse:
    uc = _resolve_dep(use_case, get_export_audit_report_use_case)
    res = uc.execute(
        profile_id=payload.profile_id,
        fai_score_data=payload.fai_score_data,
        interventions_executed=payload.interventions_executed,
    )
    return AuditReportResponse(
        profile_id=payload.profile_id,
        overall_score=Decimal(str(round(res["overall_score"], 2))),
        total_fees_saved_usd=Decimal(str(res["total_fees_saved_usd"])),
        report_markdown=res["report_markdown"],
    )
