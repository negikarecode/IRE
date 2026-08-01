import time
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("ai_observability")

class AIObservabilityTracer:
    """
    OpenTelemetry & Structured Cost/Latency Observability Tracer for AI Infrastructure.
    """
    def log_inference_span(
        self,
        tenant_id: str,
        model_id: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost_usd: float,
        metadata: Dict[str, Any] = None
    ) -> None:
        telemetry = {
            "timestamp": time.time(),
            "tenant_id": tenant_id,
            "model_id": model_id,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": latency_ms,
            "estimated_cost_usd": cost_usd,
            "metadata": metadata or {}
        }
        logger.info(f"AI_INFERENCE_SPAN {json.dumps(telemetry)}")

ai_tracer = AIObservabilityTracer()
