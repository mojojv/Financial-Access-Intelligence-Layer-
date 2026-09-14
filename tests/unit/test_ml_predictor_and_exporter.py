"""Unit tests for ML Predictive Fee Predictor and Audit Exporter."""
from uuid import uuid4

from src.application.access_index.exporter import FinancialAccessAuditReportExporter
from src.infrastructure.ml.models.fee_optimizer import ILPLiquidityFeePredictor


def test_ilp_liquidity_fee_predictor() -> None:
    predictor = ILPLiquidityFeePredictor()

    res_eur = predictor.predict_optimal_route("USD", "EUR", 100.0)
    assert res_eur.source_asset == "USD"
    assert res_eur.destination_asset == "EUR"
    assert res_eur.predicted_fee_pct < 1.0
    assert res_eur.predicted_success_probability > 90.0

    res_mxn = predictor.predict_optimal_route("USD", "MXN", 250.0)
    assert res_mxn.destination_asset == "MXN"
    assert "ILP-Latam-Direct" in res_mxn.liquidity_provider


def test_financial_access_audit_report_exporter() -> None:
    exporter = FinancialAccessAuditReportExporter()
    profile_id = uuid4()

    fai_data = {
        "overall_score": 72.5,
        "methodology": "ML_XGBOOST",
        "dimension_scores": {"access": 100, "connectivity": 95, "affordability": 80},
        "barriers": [{"barrier_code": "BAR_AFF_01"}],
    }

    interventions = [{"intervention_id": str(uuid4()), "metadata": {"estimated_savings_usd": 2.50}}]

    report = exporter.generate_report(profile_id, fai_data, interventions)
    assert report["profile_id"] == str(profile_id)
    assert report["overall_score"] == 72.5
    assert report["total_fees_saved_usd"] == 2.50
    assert "Financial Access Audit Report" in report["report_markdown"]
