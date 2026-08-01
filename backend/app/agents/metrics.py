from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class AgentMetricsSummary:
    agent_id: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_execution_time_ms: float = 0.0
    total_tool_invocations: int = 0
    tool_counts: Dict[str, int] = field(default_factory=dict)

class AgentMetricsCollector:
    """
    Telemetry Collector tracking agent performance, tool usage, and execution metrics.
    """
    def __init__(self):
        self._metrics: Dict[str, AgentMetricsSummary] = {}

    def record_run(self, agent_id: str, success: bool, duration_ms: float, tool_calls: List[str]) -> None:
        if agent_id not in self._metrics:
            self._metrics[agent_id] = AgentMetricsSummary(agent_id=agent_id)
        
        m = self._metrics[agent_id]
        m.total_runs += 1
        if success:
            m.successful_runs += 1
        else:
            m.failed_runs += 1
        m.total_execution_time_ms += duration_ms
        m.total_tool_invocations += len(tool_calls)

        for tool in tool_calls:
            m.tool_counts[tool] = m.tool_counts.get(tool, 0) + 1

    def get_metrics(self, agent_id: str) -> AgentMetricsSummary:
        return self._metrics.get(agent_id, AgentMetricsSummary(agent_id=agent_id))

agent_metrics_collector = AgentMetricsCollector()
