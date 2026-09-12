"""FastAPI API Routes for Financial Access Intelligence Layer with Graceful Fallbacks."""
from decimal import Decimal
from typing import Any, Dict, List
from uuid import UUID, uuid4

try:
    from fastapi import APIRouter, HTTPException, status
    from pydantic import BaseModel, Field
except ImportError:
    # Graceful fallback types for bare Python test environments prior to pip install
    class APIRouter:
        def get(self, *args: Any, **kwargs: Any) -> Any:
            def decorator(f: Any) -> Any: return f
            return decorator
        def post(self, *args: Any, **kwargs: Any) -> Any:
            def decorator(f: Any) -> Any: return f
            return decorator

    class BaseModel:
        def __init__(self, **data: Any) -> None:
            for k, v in data.items():
                setattr(self, k, v)

    def Field(default: Any = None, **kwargs: Any) -> Any:
        return default

from src.application.access_index.use_cases import CalculateFAIScoreUseCase
from src.application.common.dto import CalculateFAIScoreRequestDTO
from src.domain.barriers.barriers import Barrier, BarrierCode, BarrierSeverity
from src.domain.access_index.dimensions import DimensionType
from src.domain.interventions.interventions import InterventionEngine
from src.integrations.open_payments.client import MockOpenPaymentsACLAdapter
from src.infrastructure.ml.models.fee_optimizer import ILPLiquidityFeePredictor
from src.application.access_index.exporter import FinancialAccessAuditReportExporter

router = APIRouter()


class FeatureIngestionSchema(BaseModel):
    profile_id: UUID
    wallet_count: int = Field(default=1, ge=0)
    ilp_reachable: bool = Field(default=True)
    tx_success_rate: float = Field(default=0.95, ge=0.0, le=1.0)
    avg_connection_latency_ms: float = Field(default=250.0, ge=0.0)
    fee_to_volume_ratio: float = Field(default=0.01, ge=0.0)
    settlement_fulfillment_rate: float = Field(default=0.98, ge=0.0, le=1.0)
    cross_asset_success_rate: float = Field(default=0.90, ge=0.0, le=1.0)
    tx_frequency_monthly: int = Field(default=12, ge=0)
    tx_volume_monthly_usd: float = Field(default=250.0, ge=0.0)
    reserve_liquidity_usd: float = Field(default=50.0, ge=0.0)
    fallback_route_available: bool = Field(default=True)
    methodology: str = Field(default="DETERMINISTIC_RULES")


class ExecuteInterventionRequestSchema(BaseModel):
    intervention_id: UUID
    sender_wallet: str
    receiver_wallet: str
    amount: float = Field(gt=0)
    asset_code: str = Field(default="USD")


class RouteOptimizationRequestSchema(BaseModel):
    source_asset: str = Field(default="USD")
    destination_asset: str = Field(default="EUR")
    amount_usd: float = Field(default=100.0, gt=0)


class ReportExportRequestSchema(BaseModel):
    profile_id: UUID
    fai_score_data: Dict[str, Any]
    interventions_executed: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "financial-access-intelligence"}


@router.post("/api/v1/scores/calculate", tags=["FAI Scoring"])
async def calculate_fai_score(payload: FeatureIngestionSchema) -> Dict[str, Any]:
    """Calculates FAI scores and diagnoses structural barriers for a profile."""
    use_case = CalculateFAIScoreUseCase()
    request_dto = CalculateFAIScoreRequestDTO(
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
    result = use_case.execute(request_dto)
    return {
        "score_id": str(result.score_id),
        "profile_id": str(result.profile_id),
        "overall_score": result.overall_score,
        "dimension_scores": result.dimension_scores,
        "barriers": [b.__dict__ for b in result.barriers],
        "scoring_version": result.scoring_version,
        "methodology": result.methodology,
        "calculated_at": result.calculated_at,
    }


@router.post("/api/v1/interventions/recommend", tags=["Interventions"])
async def recommend_interventions(barriers_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Recommends interventions based on diagnosed barriers."""
    engine = InterventionEngine()
    domain_barriers = []

    for b in barriers_payload:
        domain_barriers.append(
            Barrier(
                barrier_id=UUID(b["barrier_id"]) if "barrier_id" in b else uuid4(),
                snapshot_id=uuid4(),
                profile_id=UUID(b["profile_id"]) if "profile_id" in b else uuid4(),
                barrier_code=BarrierCode(b["barrier_code"]),
                dimension=DimensionType(b["dimension"]),
                severity=BarrierSeverity(b["severity"]),
                evidence=b.get("evidence", {}),
            )
        )

    interventions = engine.recommend_interventions(domain_barriers)
    return {
        "interventions_count": len(interventions),
        "interventions": [
            {
                "intervention_id": str(i.intervention_id),
                "barrier_id": str(i.barrier_id),
                "profile_id": str(i.profile_id),
                "intervention_type": i.intervention_type.value,
                "status": i.status.value,
                "metadata": i.metadata,
            }
            for i in interventions
        ],
    }


@router.post("/api/v1/payments/execute", tags=["Open Payments Execution"])
async def execute_intervention_payment(payload: ExecuteInterventionRequestSchema) -> Dict[str, Any]:
    """Executes a financial intervention via Open Payments ACL."""
    from src.domain.shared.value_objects import Money, WalletAddress
    from uuid import uuid4 as _uuid4

    op_acl = MockOpenPaymentsACLAdapter()

    sender_wallet = WalletAddress(url=payload.sender_wallet)
    receiver_wallet = WalletAddress(url=payload.receiver_wallet)
    amount = Money(amount=Decimal(str(payload.amount)), asset_code=payload.asset_code, asset_scale=2)

    # 1. Resolve receiver Wallet Address metadata
    wallet_metadata = await op_acl.resolve_wallet(receiver_wallet)

    # 2. Simulate GNAP access token (in production: call authorization server)
    access_token = f"gnap-token-{_uuid4()}"

    # 3. Create Incoming Payment on receiver's resource server
    inc_payment = await op_acl.create_incoming_payment(
        wallet_address=receiver_wallet,
        amount=amount,
        access_token=access_token,
    )

    incoming_payment_id = inc_payment.get("id", f"{receiver_wallet.url}/incoming-payments/{_uuid4()}")

    # 4. Request Quote from sender's resource server
    quote = await op_acl.get_quote(
        sender_wallet=sender_wallet,
        receiver_incoming_payment_url=incoming_payment_id,
        access_token=access_token,
    )

    quote_id = quote.get("id", f"{sender_wallet.url}/quotes/{_uuid4()}")
    estimated_fee = quote.get("estimatedFee", {}).get("value", "0")

    # 5. Create Outgoing Payment
    outgoing = await op_acl.create_outgoing_payment(
        sender_wallet=sender_wallet,
        quote_url=quote_id,
        access_token=access_token,
    )

    debit_amount = outgoing.get("debitAmount", {}).get("value", "0")

    return {
        "status": "SUCCESS",
        "intervention_id": str(payload.intervention_id),
        "open_payments_outgoing_id": outgoing.get("id", ""),
        "debit_amount": float(int(debit_amount)) / 100,
        "asset_code": payload.asset_code,
        "estimated_fee": float(int(estimated_fee)) / 100,
        "wallet_metadata": wallet_metadata,
    }


@router.post("/api/v1/routes/optimize", tags=["Predictive Routing"])
async def optimize_route(payload: RouteOptimizationRequestSchema) -> Dict[str, Any]:
    """Predicts optimal Open Payments ILP route using ML fee predictor."""
    predictor = ILPLiquidityFeePredictor()
    res = predictor.predict_optimal_route(
        source_asset=payload.source_asset,
        destination_asset=payload.destination_asset,
        amount_usd=payload.amount_usd,
    )
    return res.__dict__


@router.post("/api/v1/reports/export", tags=["Audit Exporter"])
async def export_audit_report(payload: ReportExportRequestSchema) -> Dict[str, Any]:
    """Generates a downloadable Financial Access Audit Report."""
    exporter = FinancialAccessAuditReportExporter()
    res = exporter.generate_report(
        profile_id=payload.profile_id,
        fai_score_data=payload.fai_score_data,
        interventions_executed=payload.interventions_executed,
    )
    return res
