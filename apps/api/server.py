"""Zero-Dependency Native HTTP Server for Financial Access Intelligence Layer."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from uuid import UUID, uuid4

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.application.access_index.exporter import FinancialAccessAuditReportExporter
from src.application.access_index.use_cases import CalculateFAIScoreUseCase
from src.application.common.dto import CalculateFAIScoreRequestDTO
from src.domain.access_index.dimensions import DimensionType
from src.domain.barriers.barriers import Barrier, BarrierCode, BarrierSeverity
from src.domain.interventions.interventions import InterventionEngine
from src.infrastructure.ml.models.fee_optimizer import ILPLiquidityFeePredictor


class FAIServerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "healthy", "service": "financial-access-intelligence"}).encode())
        else:
            # Serve static index.html
            static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
            if os.path.exists(static_file):
                self._set_headers(200, "text/html; charset=utf-8")
                with open(static_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            payload = json.loads(post_body.decode("utf-8"))
        except Exception:
            payload = {}

        if parsed.path == "/api/v1/scores/calculate":
            use_case = CalculateFAIScoreUseCase()
            req = CalculateFAIScoreRequestDTO(
                profile_id=UUID(payload.get("profile_id", str(uuid4()))),
                wallet_count=int(payload.get("wallet_count", 1)),
                ilp_reachable=bool(payload.get("ilp_reachable", True)),
                tx_success_rate=float(payload.get("tx_success_rate", 0.95)),
                avg_connection_latency_ms=float(payload.get("avg_connection_latency_ms", 250.0)),
                fee_to_volume_ratio=float(payload.get("fee_to_volume_ratio", 0.01)),
                settlement_fulfillment_rate=float(payload.get("settlement_fulfillment_rate", 0.98)),
                cross_asset_success_rate=float(payload.get("cross_asset_success_rate", 0.90)),
                tx_frequency_monthly=int(payload.get("tx_frequency_monthly", 12)),
                tx_volume_monthly_usd=float(payload.get("tx_volume_monthly_usd", 250.0)),
                reserve_liquidity_usd=float(payload.get("reserve_liquidity_usd", 50.0)),
                fallback_route_available=bool(payload.get("fallback_route_available", True)),
                methodology=payload.get("methodology", "DETERMINISTIC_RULES"),
            )
            res = use_case.execute(req)
            data = {
                "score_id": str(res.score_id),
                "profile_id": str(res.profile_id),
                "overall_score": res.overall_score,
                "dimension_scores": res.dimension_scores,
                "barriers": [b.__dict__ for b in res.barriers],
                "scoring_version": res.scoring_version,
                "methodology": res.methodology,
                "calculated_at": res.calculated_at,
            }
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(data).encode())

        elif parsed.path == "/api/v1/interventions/recommend":
            engine = InterventionEngine()
            barriers_payload = payload if isinstance(payload, list) else []
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
            data = {
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
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(data).encode())

        elif parsed.path == "/api/v1/payments/execute":
            data = {
                "status": "SUCCESS",
                "intervention_id": str(payload.get("intervention_id", uuid4())),
                "open_payments_outgoing_id": f"https://ilp.wallet.com/alice/outgoing-payments/{uuid4()}",
                "debit_amount": float(payload.get("amount", 25.0)),
                "asset_code": payload.get("asset_code", "USD"),
                "estimated_fee": 0.50,
            }
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(data).encode())

        elif parsed.path == "/api/v1/routes/optimize":
            predictor = ILPLiquidityFeePredictor()
            res = predictor.predict_optimal_route(
                source_asset=payload.get("source_asset", "USD"),
                destination_asset=payload.get("destination_asset", "EUR"),
                amount_usd=float(payload.get("amount_usd", 100.0)),
            )
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(res.__dict__).encode())

        elif parsed.path == "/api/v1/reports/export":
            exporter = FinancialAccessAuditReportExporter()
            res = exporter.generate_report(
                profile_id=UUID(payload.get("profile_id", str(uuid4()))),
                fai_score_data=payload.get("fai_score_data", {}),
                interventions_executed=payload.get("interventions_executed", []),
            )
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(res).encode())
        else:
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Not Found"}).encode())


def run_server(port=8000):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, FAIServerHandler)
    print(f"[FAIL SERVER] Running at http://localhost:{port}/")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
