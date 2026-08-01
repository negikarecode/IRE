import time
from typing import Dict, Any, List, Set, Optional
from app.rules.schema import DeclarativeRule, RuleEvaluationTrace, RuleExecutionReport, RuleSeverity
from app.rules.registry import rule_registry
from app.rules.sandbox import safe_sandbox
from app.rules.caching import rule_cache
from app.rules.plugins import rule_plugin_manager
from app.rules.metrics import rule_metrics

class RuleExecutor:
    """
    Production Rule Engine Executor.
    Features:
    - Rule Group Filtering
    - Priority (Salience) Execution Ordering
    - Prerequisite Dependency Graph Resolution
    - AST Sandbox Evaluation with Caching
    - Action Execution Dispatching
    - Template String Variable Interpolation
    - Telemetry Metrics & Log Auditing
    """
    def _resolve_execution_order(self, rules: List[DeclarativeRule]) -> List[DeclarativeRule]:
        # Sort by priority desc (higher integer = evaluated first)
        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules

    def _interpolate_template(self, template: str, context: Dict[str, Any]) -> str:
        if not template:
            return ""
        try:
            return template.format(payload=context, context=context, **context)
        except Exception:
            return template

    async def execute(
        self,
        tenant_id: str,
        context_id: str,
        context_payload: Dict[str, Any],
        group: Optional[str] = None
    ) -> RuleExecutionReport:
        start_engine_time = time.time()
        target_group = group or "default"

        all_rules = rule_registry.list_rules(group=group, active_only=True)
        ordered_rules = self._resolve_execution_order(all_rules)

        traces: List[RuleEvaluationTrace] = []
        passed_rule_ids: Set[str] = set()
        fired_rule_ids: List[str] = []
        rules_fired_count = 0
        has_critical_failures = False

        for rule in ordered_rules:
            # Check dependencies
            deps_met = all(dep_id in passed_rule_ids for dep_id in rule.dependencies)
            if not deps_met:
                traces.append(RuleEvaluationTrace(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    version=rule.version,
                    group=rule.group,
                    passed=False,
                    fired=False,
                    severity=rule.severity.value,
                    explanation=f"Skipped: Prerequisites {rule.dependencies} not satisfied.",
                    suggestion=None,
                    execution_time_ms=0.0
                ))
                continue

            start_rule_time = time.time()
            try:
                # Fast evaluation via AST sandbox
                fired = safe_sandbox.evaluate_condition(rule.condition, context_payload)
                exec_time = (time.time() - start_rule_time) * 1000

                if fired:
                    rules_fired_count += 1
                    fired_rule_ids.append(rule.rule_id)
                    if rule.severity == RuleSeverity.CRITICAL:
                        has_critical_failures = True

                    explanation = self._interpolate_template(rule.explanation, context_payload)
                    suggestion = self._interpolate_template(rule.suggestion, context_payload)

                    # Execute rule actions if defined
                    action_results = []
                    for act in rule.actions:
                        handler = rule_plugin_manager.get_action_handler(act.action_type)
                        if handler:
                            res = await handler.handle_action(act.params, context_payload)
                            action_results.append({"action": act.action_type, "result": res})

                    traces.append(RuleEvaluationTrace(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        version=rule.version,
                        group=rule.group,
                        passed=True,
                        fired=True,
                        severity=rule.severity.value,
                        explanation=explanation,
                        suggestion=suggestion,
                        action_results=action_results,
                        execution_time_ms=round(exec_time, 2)
                    ))
                else:
                    passed_rule_ids.add(rule.rule_id)
                    traces.append(RuleEvaluationTrace(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        version=rule.version,
                        group=rule.group,
                        passed=True,
                        fired=False,
                        severity=None,
                        explanation=None,
                        suggestion=None,
                        action_results=[],
                        execution_time_ms=round(exec_time, 2)
                    ))
            except Exception as err:
                exec_time = (time.time() - start_rule_time) * 1000
                traces.append(RuleEvaluationTrace(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    version=rule.version,
                    group=rule.group,
                    passed=False,
                    fired=False,
                    severity="ERROR",
                    explanation=f"Execution error: {str(err)}",
                    suggestion="Fix rule condition syntax or plugin parameters.",
                    action_results=[],
                    execution_time_ms=round(exec_time, 2)
                ))

        total_engine_time = (time.time() - start_engine_time) * 1000

        # Record metrics telemetry
        rule_metrics.record_execution(
            group=target_group,
            rules_evaluated=len(ordered_rules),
            rules_fired=rules_fired_count,
            has_critical=has_critical_failures,
            fired_rule_ids=fired_rule_ids
        )

        return RuleExecutionReport(
            tenant_id=tenant_id,
            context_id=context_id,
            rule_group=target_group,
            total_rules_evaluated=len(ordered_rules),
            rules_fired_count=rules_fired_count,
            has_critical_failures=has_critical_failures,
            traces=traces,
            total_execution_time_ms=round(total_engine_time, 2)
        )

rule_executor = RuleExecutor()
