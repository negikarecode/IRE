from typing import Type, Callable, Optional
from app.sdk.base import BasePlugin, PluginMetadata
from app.sdk.registry import plugin_registry

def _register_decorator(extension_point: str, plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    def wrapper(cls: Type[BasePlugin]):
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            name=name,
            version=version,
            author="Founder A",
            description=description or f"Custom {extension_point} plugin",
            extension_point=extension_point
        )
        instance = cls(metadata=metadata)
        plugin_registry.register(extension_point, instance)
        return cls
    return wrapper

# 1. Rules Decorator
def register_rule(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("rules", plugin_id, name, version, description)

# 2. Validators Decorator
def register_validator(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("validators", plugin_id, name, version, description)

# 3. Risk Engine Decorator
def register_risk_engine(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("risk_engines", plugin_id, name, version, description)

# 4. Policy Provider Decorator
def register_policy_provider(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("policy_providers", plugin_id, name, version, description)

# 5. Medical Extractor Decorator
def register_medical_extractor(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("medical_extractors", plugin_id, name, version, description)

# 6. Reasoning Pipeline Decorator
def register_reasoning_pipeline(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("reasoning_pipelines", plugin_id, name, version, description)

# 7. AI Agent Decorator
def register_agent(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("agents", plugin_id, name, version, description)

# 8. Appeal Engine Decorator
def register_appeal_engine(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("appeal_engines", plugin_id, name, version, description)

# 9. Package Validator Decorator
def register_package_validator(plugin_id: str, name: str, version: str = "1.0.0", description: str = ""):
    return _register_decorator("package_validators", plugin_id, name, version, description)
