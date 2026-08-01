from typing import Dict, List, Optional
from app.rules.schema import DeclarativeRule
from app.ai.guardrails import domain_guardrail, DomainPolicyViolationException

class RuleRegistry:
    """
    Production Rule Registry managing rules by Group, Priority, and Versioning.
    Includes Domain Policy Guardrails ensuring zero hardcoded insurance/medical rules.
    """
    def __init__(self):
        # {(group, rule_id, version): DeclarativeRule}
        self._rules: Dict[tuple, DeclarativeRule] = {}
        self._register_default_rules()

    def _register_default_rules(self):
        # Generic non-domain default rules for demonstration
        self.register(DeclarativeRule(
            rule_id="RULE-GEN-001",
            name="Threshold Validation",
            version="1.0.0",
            group="validation",
            priority=100,
            condition="payload.get('amount', 0) > 10000",
            severity="WARNING",
            explanation="Transaction amount {payload[amount]} exceeds standard threshold.",
            suggestion="Route for secondary approval.",
            tags=["generic", "financial_audit"]
        ))
        self.register(DeclarativeRule(
            rule_id="RULE-GEN-002",
            name="Required Field Check",
            version="1.0.0",
            group="validation",
            priority=200,
            condition="payload.get('user_id') is None",
            severity="CRITICAL",
            explanation="Missing mandatory identifier field 'user_id'.",
            suggestion="Reject context payload.",
            tags=["generic", "data_quality"]
        ))

    def register(self, rule: DeclarativeRule) -> None:
        """
        Registers a rule definition after screening for domain policy violations.
        Strictly rejects any rule containing medical or insurance domain concepts!
        """
        domain_guardrail.enforce_policy(rule.condition, context_name=f"Rule '{rule.rule_id}' Condition")
        domain_guardrail.enforce_policy(rule.explanation, context_name=f"Rule '{rule.rule_id}' Explanation")
        domain_guardrail.enforce_policy(rule.suggestion, context_name=f"Rule '{rule.rule_id}' Suggestion")

        key = (rule.group, rule.rule_id, rule.version)
        self._rules[key] = rule

    def unregister(self, rule_id: str, version: str = "1.0.0", group: str = "default") -> bool:
        key = (group, rule_id, version)
        if key in self._rules:
            del self._rules[key]
            return True
        return False

    def get_rule(self, rule_id: str, version: str = "1.0.0", group: str = "default") -> Optional[DeclarativeRule]:
        return self._rules.get((group, rule_id, version))

    def list_rules(
        self,
        group: Optional[str] = None,
        active_only: bool = True,
        tag: Optional[str] = None
    ) -> List[DeclarativeRule]:
        rules = list(self._rules.values())

        if group:
            rules = [r for r in rules if r.group == group]
        if active_only:
            rules = [r for r in rules if r.is_active]
        if tag:
            rules = [r for r in rules if tag in r.tags]

        # Priority / Salience sorting (higher priority evaluated first)
        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules

    def list_groups(self) -> List[str]:
        groups = set(r.group for r in self._rules.values())
        return list(groups)

    def clear(self) -> None:
        self._rules.clear()

rule_registry = RuleRegistry()
