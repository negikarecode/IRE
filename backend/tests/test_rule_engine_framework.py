import pytest
import asyncio
import json

from app.rules.schema import DeclarativeRule, RuleSeverity, RuleAction
from app.rules.registry import rule_registry, RuleRegistry
from app.rules.loader import rule_loader
from app.rules.executor import rule_executor
from app.rules.sandbox import safe_sandbox
from app.rules.plugins import rule_plugin_manager, IRulePlugin, IRuleActionHandler
from app.rules.caching import rule_cache
from app.rules.metrics import rule_metrics
from app.rules.testing import rule_testing_suite, RuleTestCase
from app.ai.guardrails import DomainPolicyViolationException

def run_async(coro):
    return asyncio.run(coro)

# 1. Test Domain Guardrail in Rule Registry (Zero Insurance Rules constraint)
def test_rule_registry_insurance_rejection():
    insurance_rule = DeclarativeRule(
        rule_id="INS_RULE_001",
        name="Insurance Policy Claim Check",
        group="claims",
        condition="payload.claim_amount > payload.policy_deductible",
        severity=RuleSeverity.WARNING,
        explanation="Claim exceeds policy deductible limit."
    )
    with pytest.raises(DomainPolicyViolationException) as exc_info:
        rule_registry.register(insurance_rule)
    assert "Insurance domain content detected" in str(exc_info.value)

# 2. Test Rule Registry & Versioning & Groups
def test_rule_registry_groups_and_versioning():
    r1 = DeclarativeRule(
        rule_id="RULE-SEC-01",
        name="IP Access Control",
        version="1.0.0",
        group="security",
        priority=150,
        condition="payload.get('ip') == '127.0.0.1'",
        tags=["security", "audit"]
    )
    r2 = DeclarativeRule(
        rule_id="RULE-SEC-01",
        name="IP Access Control V2",
        version="1.1.0",
        group="security",
        priority=200,
        condition="payload.get('ip') in ['127.0.0.1', '10.0.0.1']",
        tags=["security", "audit"]
    )
    rule_registry.register(r1)
    rule_registry.register(r2)

    sec_rules = rule_registry.list_rules(group="security")
    assert len(sec_rules) >= 2
    # Verify priority sorting (priority 200 before 150)
    assert sec_rules[0].priority == 200

    lookup_v1 = rule_registry.get_rule("RULE-SEC-01", version="1.0.0", group="security")
    assert lookup_v1 is not None
    assert lookup_v1.version == "1.0.0"

# 3. Test Rule Loader (Dynamic JSON import)
def test_rule_loader_json():
    json_data = json.dumps([
        {
            "rule_id": "RULE-DYN-01",
            "name": "Dynamic Limit Verification",
            "version": "1.0.0",
            "group": "finance",
            "priority": 300,
            "condition": "payload.get('balance', 0) < 0",
            "severity": "CRITICAL",
            "explanation": "Account balance {payload[balance]} is negative.",
            "suggestion": "Freeze account transactions.",
            "tags": ["finance", "overdraft"]
        }
    ])

    loaded = rule_loader.load_from_json_string(json_data)
    assert len(loaded) == 1
    assert loaded[0].rule_id == "RULE-DYN-01"
    assert loaded[0].group == "finance"

# 4. Test Safe Sandbox & Plugins
def test_safe_sandbox_and_plugins():
    # Test allowed AST math & logic
    ctx = {"amount": 500, "status": "ACTIVE"}
    assert safe_sandbox.evaluate_condition("payload['amount'] > 100 and payload['status'] == 'ACTIVE'", ctx) is True

    # Test custom plugin function (regex_match)
    ctx_regex = {"email": "user@example.com"}
    assert safe_sandbox.evaluate_condition("regex_match('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\\\.[a-zA-Z0-9-.]+$', payload['email'])", ctx_regex) is True

    # Test forbidden syntax (import attempt)
    with pytest.raises(ValueError):
        safe_sandbox.evaluate_condition("__import__('os').system('ls')", ctx)

# 5. Test Rule Executor & Priority & Actions
def test_rule_executor_and_actions():
    async def _test():
        # Clear & register clean test rules
        rule_registry.clear()

        r_low = DeclarativeRule(
            rule_id="RULE-LOW",
            name="Low Priority Rule",
            group="exec_test",
            priority=50,
            condition="payload.get('score', 0) > 10",
            severity=RuleSeverity.INFO,
            explanation="Score {payload[score]} > 10."
        )
        r_high = DeclarativeRule(
            rule_id="RULE-HIGH",
            name="High Priority Rule",
            group="exec_test",
            priority=250,
            condition="payload.get('score', 0) > 80",
            severity=RuleSeverity.CRITICAL,
            explanation="High score {payload[score]} detected.",
            actions=[RuleAction(action_type="log_alert", params={"message": "High score alert!"})]
        )

        rule_registry.register(r_low)
        rule_registry.register(r_high)

        payload = {"score": 95}
        report = await rule_executor.execute(
            tenant_id="tenant_test",
            context_id="ctx_101",
            context_payload=payload,
            group="exec_test"
        )

        assert report.total_rules_evaluated == 2
        assert report.rules_fired_count == 2
        assert report.has_critical_failures is True

        # Check trace execution order (high priority evaluated first)
        assert report.traces[0].rule_id == "RULE-HIGH"
        assert report.traces[1].rule_id == "RULE-LOW"
        assert report.traces[0].action_results[0]["result"]["status"] == "logged"

    run_async(_test())

# 6. Test Rule Cache
def test_rule_cache():
    rule_cache.clear()
    cond = "payload.get('tier') == 'GOLD'"
    
    # First compilation (miss)
    c1 = rule_cache.get_or_compile(cond)
    assert c1 is not None

    # Second fetch (hit)
    c2 = rule_cache.get_or_compile(cond)
    assert c2 is not None

    stats = rule_cache.get_stats()
    assert stats["hits"] == 1

# 7. Test Rule Testing Suite
def test_rule_testing_suite():
    rule = DeclarativeRule(
        rule_id="RULE-TEST-01",
        name="Age Verification",
        condition="payload.get('age', 0) >= 18"
    )

    test_cases = [
        RuleTestCase(test_id="t1", mock_payload={"age": 21}, expected_fired=True),
        RuleTestCase(test_id="t2", mock_payload={"age": 15}, expected_fired=False)
    ]

    results = rule_testing_suite.run_tests(rule, test_cases)
    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is True

# 8. Test Rule Metrics Telemetry
def test_rule_metrics():
    rule_metrics.reset()
    rule_metrics.record_execution("finance", rules_evaluated=5, rules_fired=2, has_critical=False, fired_rule_ids=["R1", "R2"])
    
    m = rule_metrics.get_metrics()
    assert m["total_engine_evaluations"] == 1
    assert m["total_rules_fired"] == 2
    assert m["group_executions"]["finance"] == 1
