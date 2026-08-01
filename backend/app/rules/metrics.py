from typing import Dict, Any
from collections import defaultdict
import time

class RuleMetricsManager:
    """
    Telemetry and Monitoring Metrics Manager for Rule Engine Framework.
    Tracks execution throughput, rule firing frequencies, latencies, and critical alerts.
    """
    def __init__(self):
        self.total_evaluations = 0
        self.total_rules_evaluated = 0
        self.total_rules_fired = 0
        self.total_critical_failures = 0
        self.rule_fire_counts: Dict[str, int] = defaultdict(int)
        self.group_execution_counts: Dict[str, int] = defaultdict(int)

    def record_execution(
        self,
        group: str,
        rules_evaluated: int,
        rules_fired: int,
        has_critical: bool,
        fired_rule_ids: list
    ) -> None:
        self.total_evaluations += 1
        self.total_rules_evaluated += rules_evaluated
        self.total_rules_fired += rules_fired
        if has_critical:
            self.total_critical_failures += 1

        self.group_execution_counts[group] += 1
        for r_id in fired_rule_ids:
            self.rule_fire_counts[r_id] += 1

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_engine_evaluations": self.total_evaluations,
            "total_rules_evaluated": self.total_rules_evaluated,
            "total_rules_fired": self.total_rules_fired,
            "total_critical_failures": self.total_critical_failures,
            "group_executions": dict(self.group_execution_counts),
            "top_fired_rules": dict(sorted(self.rule_fire_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }

    def reset(self) -> None:
        self.total_evaluations = 0
        self.total_rules_evaluated = 0
        self.total_rules_fired = 0
        self.total_critical_failures = 0
        self.rule_fire_counts.clear()
        self.group_execution_counts.clear()

rule_metrics = RuleMetricsManager()
