"""Use Cases for Financial Access Index Calculation and Barrier Diagnosis."""
from src.application.common.dto import (
    CalculateFAIScoreRequestDTO,
    FAIScoreResponseDTO,
    BarrierResponseDTO,
)
from src.domain.access_index.scoring import (
    FeatureVector,
    IFAIScoringEngine,
    DeterministicRuleScoringEngine,
)
from src.domain.barriers.barriers import BarrierDetectionService


class CalculateFAIScoreUseCase:
    """Use Case Orchestrator for calculating FAI and diagnosing structural barriers."""

    def __init__(
        self,
        scoring_engine: IFAIScoringEngine = None,
        barrier_detector: BarrierDetectionService = None,
    ) -> None:
        self.scoring_engine = scoring_engine or DeterministicRuleScoringEngine()
        self.barrier_detector = barrier_detector or BarrierDetectionService()

    def execute(self, request: CalculateFAIScoreRequestDTO) -> FAIScoreResponseDTO:
        # 1. Map DTO to Domain FeatureVector
        features = FeatureVector(
            wallet_count=request.wallet_count,
            ilp_reachable=request.ilp_reachable,
            tx_success_rate=request.tx_success_rate,
            avg_connection_latency_ms=request.avg_connection_latency_ms,
            fee_to_volume_ratio=request.fee_to_volume_ratio,
            settlement_fulfillment_rate=request.settlement_fulfillment_rate,
            cross_asset_success_rate=request.cross_asset_success_rate,
            tx_frequency_monthly=request.tx_frequency_monthly,
            tx_volume_monthly_usd=request.tx_volume_monthly_usd,
            reserve_liquidity_usd=request.reserve_liquidity_usd,
            fallback_route_available=request.fallback_route_available,
        )

        # 2. Calculate FAI Score
        fai_score = self.scoring_engine.calculate_score(
            profile_id=request.profile_id,
            features=features,
        )

        # 3. Detect Barriers
        barriers = self.barrier_detector.detect_barriers(fai_score)

        # 4. Map to Response DTO
        barrier_dtos = [
            BarrierResponseDTO(
                barrier_id=b.barrier_id,
                barrier_code=b.barrier_code.value,
                dimension=b.dimension.value,
                severity=b.severity.value,
                evidence=b.evidence,
            )
            for b in barriers
        ]

        dim_scores_map = {
            dim.value: float(score_vo.score)
            for dim, score_vo in fai_score.dimension_scores.items()
        }

        return FAIScoreResponseDTO(
            score_id=fai_score.score_id,
            profile_id=fai_score.profile_id,
            overall_score=float(fai_score.overall_score),
            dimension_scores=dim_scores_map,
            barriers=barrier_dtos,
            scoring_version=fai_score.scoring_version,
            calculated_at=fai_score.calculated_at.isoformat(),
        )
