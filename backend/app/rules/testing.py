from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from app.rules.schema import DeclarativeRule
from app.rules.sandbox import safe_sandbox

@dataclass
class RuleTestCase:
    test_id: str
    mock_payload: Dict[str, Any]
    expected_fired: bool
    description: str = ""

@dataclass
class RuleTestResult:
    test_id: str
    passed: bool
    expected_fired: bool
    actual_fired: bool
    error_message: Optional[str] = None

class RuleTestingSuite:
    """
    Automated Testing Suite for rule developers to test rule logic in isolation.
    """
    def run_tests(self, rule: DeclarativeRule, test_cases: List[RuleTestCase]) -> List[RuleTestResult]:
        results = []
        for tc in test_cases:
            try:
                actual_fired = safe_sandbox.evaluate_condition(rule.condition, tc.mock_payload)
                passed = (actual_fired == tc.expected_fired)
                results.append(RuleTestResult(
                    test_id=tc.test_id,
                    passed=passed,
                    expected_fired=tc.expected_fired,
                    actual_fired=actual_fired
                ))
            except Exception as e:
                results.append(RuleTestResult(
                    test_id=tc.test_id,
                    passed=False,
                    expected_fired=tc.expected_fired,
                    actual_fired=False,
                    error_message=str(e)
                ))
        return results

rule_testing_suite = RuleTestingSuite()
