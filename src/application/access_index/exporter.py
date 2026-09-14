"""Financial Access Audit Report Generator."""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


class FinancialAccessAuditReportExporter:
    """Generates comprehensive Financial Access Audit Reports for researchers and auditors."""

    def generate_report(
        self,
        profile_id: UUID,
        fai_score_data: dict[str, Any],
        interventions_executed: list[dict[str, Any]],
    ) -> dict[str, Any]:
        overall_score = fai_score_data.get("overall_score", 0.0)

        # Classify inclusion level
        if overall_score >= 80.0:
            inclusion_tier = "TIER_1_FULLY_INCLUDED"
            recommendation = "Maintain current wallet infrastructure and liquidity reserves."
        elif overall_score >= 50.0:
            inclusion_tier = "TIER_2_MODERATELY_INCLUDED"
            recommendation = "Execute fee optimization routing and add secondary fallback Wallet Address."
        else:
            inclusion_tier = "TIER_3_SEVERELY_CONSTRAINED"
            recommendation = "High priority intervention required: Route via zero-fee ILP bridge and establish liquidity pool."

        # Calculate cumulative savings
        total_fees_saved = sum(i.get("metadata", {}).get("estimated_savings_usd", 0.50) for i in interventions_executed)

        timestamp = datetime.now(UTC).isoformat()

        report_markdown = f"""# Financial Access Audit Report
**Profile ID**: `{profile_id}`  
**Generated At**: {timestamp}  
**Inclusion Tier**: `{inclusion_tier}`  
**Overall FAI Score**: **{overall_score} / 100** ({fai_score_data.get('methodology', 'ML_XGBOOST')})

---

### 📊 7 Dimensions Breakdown
"""
        for dim, score in fai_score_data.get("dimension_scores", {}).items():
            report_markdown += f"- **{dim.capitalize()}**: `{score} / 100`\n"

        report_markdown += f"""
---

### 🛡 Diagnosed Barriers & Interventions
- **Active Barriers Diagnosed**: {len(fai_score_data.get('barriers', []))}
- **Interventions Executed**: {len(interventions_executed)}
- **Estimated Total Cost Saved**: `${total_fees_saved:.2f} USD`

### 💡 Strategic Recommendation
{recommendation}
"""

        return {
            "profile_id": str(profile_id),
            "generated_at": timestamp,
            "inclusion_tier": inclusion_tier,
            "overall_score": overall_score,
            "total_fees_saved_usd": round(total_fees_saved, 2),
            "report_markdown": report_markdown,
        }
