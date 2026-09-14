"""Threshold-Based Barrier Evaluator Component."""
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from src.domain.access_index.dimensions import FinancialScore
from src.domain.barriers.barriers import Barrier, BarrierSeverity, BarrierState
from src.domain.shared.value_objects import BarrierCode, DimensionKey


@dataclass(frozen=True)
class BarrierThresholdConfig:
    """Configurable threshold rules for diagnosing barriers."""
    affordability_threshold: Decimal = Decimal("40.00")
    interoperability_threshold: Decimal = Decimal("45.00")
    resilience_threshold: Decimal = Decimal("35.00")
    connectivity_threshold: Decimal = Decimal("50.00")
    access_threshold: Decimal = Decimal("50.00")
    usage_threshold: Decimal = Decimal("30.00")
    reliability_threshold: Decimal = Decimal("50.00")


class BarrierEvaluator:
    """Threshold-Based Engine that evaluates FAI dimension scores to diagnose structural barriers."""

    def __init__(self, config: BarrierThresholdConfig | None = None) -> None:
        self.config = config or BarrierThresholdConfig()

    def evaluate_barriers(self, fai_score: FinancialScore) -> list[Barrier]:
        barriers: list[Barrier] = []
        dims = fai_score.dimensions

        # 1. Evaluate Affordability (High Fee Burden)
        if DimensionKey.AFFORDABILITY in dims:
            aff_score = dims[DimensionKey.AFFORDABILITY].score.value
            if aff_score < self.config.affordability_threshold:
                barriers.append(
                    Barrier(
                        barrier_id=uuid4(),
                        snapshot_id=fai_score.score_id,
                        profile_id=fai_score.profile_id,
                        barrier_code=BarrierCode.HIGH_FEE_BURDEN,
                        dimension=DimensionKey.AFFORDABILITY,
                        severity=BarrierSeverity.HIGH if aff_score < Decimal("20.00") else BarrierSeverity.MEDIUM,
                        evidence={"affordability_score": str(aff_score), "threshold": str(self.config.affordability_threshold)},
                        state=BarrierState.DIAGNOSED,
                    )
                )

        # 2. Evaluate Interoperability (Low Cross-Asset Conversion)
        if DimensionKey.INTEROPERABILITY in dims:
            int_score = dims[DimensionKey.INTEROPERABILITY].score.value
            if int_score < self.config.interoperability_threshold:
                barriers.append(
                    Barrier(
                        barrier_id=uuid4(),
                        snapshot_id=fai_score.score_id,
                        profile_id=fai_score.profile_id,
                        barrier_code=BarrierCode.LOW_INTEROPERABILITY,
                        dimension=DimensionKey.INTEROPERABILITY,
                        severity=BarrierSeverity.HIGH if int_score < Decimal("25.00") else BarrierSeverity.MEDIUM,
                        evidence={"interoperability_score": str(int_score), "threshold": str(self.config.interoperability_threshold)},
                        state=BarrierState.DIAGNOSED,
                    )
                )

        # 3. Evaluate Resilience (Low Liquidity Buffer)
        if DimensionKey.RESILIENCE in dims:
            res_score = dims[DimensionKey.RESILIENCE].score.value
            if res_score < self.config.resilience_threshold:
                barriers.append(
                    Barrier(
                        barrier_id=uuid4(),
                        snapshot_id=fai_score.score_id,
                        profile_id=fai_score.profile_id,
                        barrier_code=BarrierCode.LOW_RESILIENCE,
                        dimension=DimensionKey.RESILIENCE,
                        severity=BarrierSeverity.MEDIUM,
                        evidence={"resilience_score": str(res_score), "threshold": str(self.config.resilience_threshold)},
                        state=BarrierState.DIAGNOSED,
                    )
                )

        # 4. Evaluate Connectivity (High Latency / Low Success Rate)
        if DimensionKey.CONNECTIVITY in dims:
            conn_score = dims[DimensionKey.CONNECTIVITY].score.value
            if conn_score < self.config.connectivity_threshold:
                barriers.append(
                    Barrier(
                        barrier_id=uuid4(),
                        snapshot_id=fai_score.score_id,
                        profile_id=fai_score.profile_id,
                        barrier_code=BarrierCode.UNRELIABLE_CONNECTIVITY,
                        dimension=DimensionKey.CONNECTIVITY,
                        severity=BarrierSeverity.HIGH if conn_score < Decimal("30.00") else BarrierSeverity.MEDIUM,
                        evidence={"connectivity_score": str(conn_score), "threshold": str(self.config.connectivity_threshold)},
                        state=BarrierState.DIAGNOSED,
                    )
                )

        # 5. Evaluate Access (Unreachable Wallet)
        if DimensionKey.ACCESS in dims:
            acc_score = dims[DimensionKey.ACCESS].score.value
            if acc_score < self.config.access_threshold:
                barriers.append(
                    Barrier(
                        barrier_id=uuid4(),
                        snapshot_id=fai_score.score_id,
                        profile_id=fai_score.profile_id,
                        barrier_code=BarrierCode.LIMITED_ACCESS,
                        dimension=DimensionKey.ACCESS,
                        severity=BarrierSeverity.CRITICAL if acc_score == Decimal("0.00") else BarrierSeverity.HIGH,
                        evidence={"access_score": str(acc_score), "threshold": str(self.config.access_threshold)},
                        state=BarrierState.DIAGNOSED,
                    )
                )

        # 6. Evaluate Usage (Inactive Telemetry)
        if DimensionKey.USAGE in dims:
            usg_score = dims[DimensionKey.USAGE].score.value
            if usg_score < self.config.usage_threshold:
                barriers.append(
                    Barrier(
                        barrier_id=uuid4(),
                        snapshot_id=fai_score.score_id,
                        profile_id=fai_score.profile_id,
                        barrier_code=BarrierCode.LOW_USAGE,
                        dimension=DimensionKey.USAGE,
                        severity=BarrierSeverity.LOW if usg_score > Decimal("15.00") else BarrierSeverity.MEDIUM,
                        evidence={"usage_score": str(usg_score), "threshold": str(self.config.usage_threshold)},
                        state=BarrierState.DIAGNOSED,
                    )
                )

        # 7. Evaluate Reliability (Settlement Fulfillment Issues)
        if DimensionKey.RELIABILITY in dims:
            rel_score = dims[DimensionKey.RELIABILITY].score.value
            if rel_score < self.config.reliability_threshold:
                barriers.append(
                    Barrier(
                        barrier_id=uuid4(),
                        snapshot_id=fai_score.score_id,
                        profile_id=fai_score.profile_id,
                        barrier_code=BarrierCode.UNRELIABLE_SETTLEMENT,
                        dimension=DimensionKey.RELIABILITY,
                        severity=BarrierSeverity.HIGH if rel_score < Decimal("25.00") else BarrierSeverity.MEDIUM,
                        evidence={"reliability_score": str(rel_score), "threshold": str(self.config.reliability_threshold)},
                        state=BarrierState.DIAGNOSED,
                    )
                )

        return barriers
