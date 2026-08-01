from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class RuleAction:
    """
    Action specification triggered when a rule condition evaluates to True.
    """
    action_type: str        # e.g., "set_field", "trigger_event", "log_alert", "webhook"
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeclarativeRule:
    """
    Production-Grade Pure Declarative Rule Specification.
    Zero domain rules hardcoded. Fully configurable by external developers/APIs.
    """
    rule_id: str
    name: str
    version: str = "1.0.0"
    group: str = "default"
    priority: int = 100     # Salience: Higher integer = evaluated first
    condition: str = "True" # Pythonic safe AST condition, e.g., "payload.amount > 5000 and payload.status == 'PENDING'"
    severity: RuleSeverity = RuleSeverity.WARNING
    explanation: str = ""   # Templated explanation, e.g., "Transaction amount {payload.amount} exceeded threshold."
    suggestion: str = ""    # Templated suggestion, e.g., "Flag for manual supervisor audit."
    actions: List[RuleAction] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Prerequisite rule IDs
    is_active: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass
class RuleEvaluationTrace:
    rule_id: str
    rule_name: str
    version: str
    group: str
    passed: bool            # True if evaluated without error (whether fired or not)
    fired: bool             # True if condition evaluated to True
    severity: Optional[str]
    explanation: Optional[str]
    suggestion: Optional[str]
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0

@dataclass
class RuleExecutionReport:
    tenant_id: str
    context_id: str
    rule_group: str
    total_rules_evaluated: int
    rules_fired_count: int
    has_critical_failures: bool
    traces: List[RuleEvaluationTrace]
    total_execution_time_ms: float = 0.0
