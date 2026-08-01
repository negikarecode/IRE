import os
import sys
import importlib.util
import inspect
from typing import List, Dict, Any, Optional
from app.sdk.base import BasePlugin
from app.sdk.registry import plugin_registry

class PluginDiscoveryEngine:
    """
    Automatic Plugin Discovery Engine.
    Scans specified directories for Founder A plugins, dynamically loads modules via importlib,
    and registers all discovered plugins automatically without modifying backend platform code.
    """
    def __init__(self, plugin_directories: Optional[List[str]] = None):
        self.plugin_directories = plugin_directories or [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../plugins")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../plugins"))
        ]

    def discover_and_load(self) -> Dict[str, Any]:
        discovered_modules = []
        loaded_count = 0

        for plugin_dir in self.plugin_directories:
            if not os.path.exists(plugin_dir):
                continue

            for root, _, files in os.walk(plugin_dir):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        file_path = os.path.join(root, file)
                        module_name = f"custom_plugin_{os.path.splitext(file)[0]}"

                        try:
                            spec = importlib.util.spec_from_file_location(module_name, file_path)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                sys.modules[module_name] = module
                                spec.loader.exec_module(module)
                                discovered_modules.append(module_name)
                                loaded_count += 1
                        except Exception as e:
                            print(f"[SDK Plugin Discovery Warning] Failed to load plugin '{file_path}': {e}")

        all_plugins = plugin_registry.list_plugins()
        return {
            "status": "DISCOVERY_COMPLETE",
            "discovered_modules": discovered_modules,
            "total_modules_loaded": loaded_count,
            "registered_plugins_count": len(all_plugins),
            "plugins": [p.plugin_id for p in all_plugins]
        }

plugin_discovery_engine = PluginDiscoveryEngine()
