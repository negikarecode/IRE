"""
Generic Declarative Rule Engine Framework Package
Provides Rule Registry, Loader, Executor, Sandbox, Priority, Groups, Versioning,
Testing Suite, Extension Plugins, Database Persistence, AST Cache, Telemetry Metrics,
and Execution Logs.
Strictly ZERO insurance rules. Pure Infrastructure.
"""

from app.rules.schema import (
    DeclarativeRule,
    RuleSeverity,
    RuleAction,
    RuleEvaluationTrace,
    RuleExecutionReport
)
from app.rules.registry import rule_registry, RuleRegistry
from app.rules.loader import rule_loader, RuleLoader
from app.rules.executor import rule_executor, RuleExecutor
from app.rules.sandbox import safe_sandbox, SafeRuleSandbox
from app.rules.plugins import (
    rule_plugin_manager,
    RulePluginManager,
    IRulePlugin,
    IRuleActionHandler
)
from app.rules.caching import rule_cache, RuleCacheManager
from app.rules.metrics import rule_metrics, RuleMetricsManager
from app.rules.testing import (
    rule_testing_suite,
    RuleTestingSuite,
    RuleTestCase,
    RuleTestResult
)
from app.rules.marketplace import rule_marketplace, RuleMarketplaceRegistry, RuleMarketplacePackage

__all__ = [
    "DeclarativeRule",
    "RuleSeverity",
    "RuleAction",
    "RuleEvaluationTrace",
    "RuleExecutionReport",
    "rule_registry",
    "RuleRegistry",
    "rule_loader",
    "RuleLoader",
    "rule_executor",
    "RuleExecutor",
    "safe_sandbox",
    "SafeRuleSandbox",
    "rule_plugin_manager",
    "RulePluginManager",
    "IRulePlugin",
    "IRuleActionHandler",
    "rule_cache",
    "RuleCacheManager",
    "rule_metrics",
    "RuleMetricsManager",
    "rule_testing_suite",
    "RuleTestingSuite",
    "RuleTestCase",
    "RuleTestResult",
    "rule_marketplace",
    "RuleMarketplaceRegistry",
    "RuleMarketplacePackage"
]
