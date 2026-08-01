from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time

@dataclass
class PluginMetadata:
    """
    Metadata describing a Founder A Business Logic Plugin.
    """
    plugin_id: str
    name: str
    version: str = "1.0.0"
    author: str = "Founder A"
    description: str = "Custom Business Logic Plugin"
    extension_point: str = "generic"
    enabled: bool = True
    created_at: float = field(default_factory=time.time)

class BasePlugin(ABC):
    """
    Abstract Base Class for ALL Business Logic Plugins.
    Founder A inherits from this class or extension point base classes.
    """
    metadata: PluginMetadata

    def __init__(self, metadata: Optional[PluginMetadata] = None):
        if metadata:
            self.metadata = metadata

    @abstractmethod
    async def initialize(self) -> bool:
        """Called when the plugin is loaded during auto-discovery."""
        return True

    @abstractmethod
    async def shutdown(self) -> None:
        """Called when the plugin is unloaded."""
        pass
