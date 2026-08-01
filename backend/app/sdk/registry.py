from typing import Dict, List, Optional, Any, Type
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

class PluginRegistry:
    """
    Central Registry managing Founder A Business Logic Plugins across all 9 Extension Points.
    The platform uses this registry to discover, load, and execute plugins dynamically.
    """
    def __init__(self):
        self._plugins: Dict[str, Dict[str, BasePlugin]] = {
            "rules": {},
            "validators": {},
            "risk_engines": {},
            "policy_providers": {},
            "medical_extractors": {},
            "reasoning_pipelines": {},
            "agents": {},
            "appeal_engines": {},
            "package_validators": {}
        }

    def register(self, extension_point: str, plugin: BasePlugin) -> None:
        if extension_point not in self._plugins:
            self._plugins[extension_point] = {}
        
        plugin_id = plugin.metadata.plugin_id
        self._plugins[extension_point][plugin_id] = plugin

    def get(self, extension_point: str, plugin_id: str) -> Optional[BasePlugin]:
        return self._plugins.get(extension_point, {}).get(plugin_id)

    def list_plugins(self, extension_point: Optional[str] = None) -> List[PluginMetadata]:
        if extension_point:
            return [p.metadata for p in self._plugins.get(extension_point, {}).values()]
        
        all_metadata = []
        for point_dict in self._plugins.values():
            for p in point_dict.values():
                all_metadata.append(p.metadata)
        return all_metadata

    async def execute(self, extension_point: str, plugin_id: str, method_name: str, *args, **kwargs) -> Any:
        plugin = self.get(extension_point, plugin_id)
        if not plugin:
            raise KeyError(f"Plugin '{plugin_id}' not found under extension point '{extension_point}'.")
        
        if not plugin.metadata.enabled:
            raise RuntimeError(f"Plugin '{plugin_id}' is currently disabled.")

        method = getattr(plugin, method_name, None)
        if not method or not callable(method):
            raise AttributeError(f"Method '{method_name}' not found on plugin '{plugin_id}'.")

        return await method(*args, **kwargs)

plugin_registry = PluginRegistry()
