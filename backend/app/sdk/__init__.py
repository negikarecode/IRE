"""
Founder A Business Logic SDK Package
Enables Founder A to create custom business rules, validators, risk engines, policy providers,
medical extractors, reasoning pipelines, AI agents, appeal engines, and package validators
WITHOUT modifying backend platform code.
The platform automatically discovers and loads all custom plugins at runtime.
"""

from app.sdk.base import BasePlugin, PluginMetadata
from app.sdk.extension_points import (
    BaseRulePlugin,
    BaseValidatorPlugin,
    BaseRiskEnginePlugin,
    BasePolicyProviderPlugin,
    BaseMedicalExtractorPlugin,
    BaseReasoningPipelinePlugin,
    BaseAgentPlugin,
    BaseAppealEnginePlugin,
    BasePackageValidatorPlugin
)
from app.sdk.decorators import (
    register_rule,
    register_validator,
    register_risk_engine,
    register_policy_provider,
    register_medical_extractor,
    register_reasoning_pipeline,
    register_agent,
    register_appeal_engine,
    register_package_validator
)
from app.sdk.registry import plugin_registry, PluginRegistry
from app.sdk.discovery import plugin_discovery_engine, PluginDiscoveryEngine

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "BaseRulePlugin",
    "BaseValidatorPlugin",
    "BaseRiskEnginePlugin",
    "BasePolicyProviderPlugin",
    "BaseMedicalExtractorPlugin",
    "BaseReasoningPipelinePlugin",
    "BaseAgentPlugin",
    "BaseAppealEnginePlugin",
    "BasePackageValidatorPlugin",
    "register_rule",
    "register_validator",
    "register_risk_engine",
    "register_policy_provider",
    "register_medical_extractor",
    "register_reasoning_pipeline",
    "register_agent",
    "register_appeal_engine",
    "register_package_validator",
    "plugin_registry",
    "PluginRegistry",
    "plugin_discovery_engine",
    "PluginDiscoveryEngine"
]
