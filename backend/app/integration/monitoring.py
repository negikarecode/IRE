from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class ConnectorTelemetrySummary:
    connector_id: str
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    total_sent: int = 0
    total_received: int = 0
    total_errors: int = 0
    average_latency_ms: float = 0.0

class IntegrationMonitoring:
    """
    Monitoring Telemetry & Health Tracker for Enterprise Integration Connectors.
    """
    def __init__(self):
        self._telemetry: Dict[str, ConnectorTelemetrySummary] = {}

    def record_metrics(self, connector_id: str, success: bool, latency_ms: float) -> None:
        if connector_id not in self._telemetry:
            self._telemetry[connector_id] = ConnectorTelemetrySummary(connector_id=connector_id, status="HEALTHY")
        
        t = self._telemetry[connector_id]
        t.total_sent += 1
        if not success:
            t.total_errors += 1
            if t.total_errors >= 5:
                t.status = "UNHEALTHY"
            elif t.total_errors >= 2:
                t.status = "DEGRADED"

        # Exponential moving average for latency
        t.average_latency_ms = round((t.average_latency_ms * 0.8) + (latency_ms * 0.2), 2)

    def get_status(self, connector_id: str) -> ConnectorTelemetrySummary:
        return self._telemetry.get(connector_id, ConnectorTelemetrySummary(connector_id=connector_id, status="UNKNOWN"))

    def list_all(self) -> List[ConnectorTelemetrySummary]:
        return list(self._telemetry.values())

integration_monitoring = IntegrationMonitoring()
