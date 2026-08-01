from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Callable, Optional, List
import time
import json

@dataclass
class AgentToolSpec:
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Any]
    timeout_seconds: float = 30.0

class BaseAgentTool(ABC):
    """
    Abstract Base Class for Enterprise Agent Tools.
    Future developers subclass this to add custom tools without altering core framework.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    @abstractmethod
    def run(self, params: Dict[str, Any]) -> Any:
        pass

# Built-in Default Agent Tools
class HttpRequestTool(BaseAgentTool):
    @property
    def name(self) -> str:
        return "http_request"

    @property
    def description(self) -> str:
        return "Executes HTTP API request to external REST endpoints"

    def run(self, params: Dict[str, Any]) -> Any:
        url = params.get("url", "https://api.example.com/data")
        method = params.get("method", "GET")
        return {"status": 200, "url": url, "method": method, "data": {"message": "HTTP Tool Response"}}

class DataTransformTool(BaseAgentTool):
    @property
    def name(self) -> str:
        return "data_transform"

    @property
    def description(self) -> str:
        return "Transforms JSON payloads, extracts fields, or formats string output"

    def run(self, params: Dict[str, Any]) -> Any:
        input_data = params.get("data", {})
        return {"status": "transformed", "processed_keys": list(input_data.keys()) if isinstance(input_data, dict) else [str(input_data)]}

class MathSolverTool(BaseAgentTool):
    @property
    def name(self) -> str:
        return "math_solver"

    @property
    def description(self) -> str:
        return "Evaluates mathematical expressions and data calculations"

    def run(self, params: Dict[str, Any]) -> Any:
        expr = str(params.get("expression", "0"))
        # Safe math calculation
        try:
            val = eval(expr, {"__builtins__": {}}, {"abs": abs, "min": min, "max": max, "sum": sum, "round": round})
            return {"expression": expr, "result": val}
        except Exception as e:
            return {"expression": expr, "error": str(e)}

class ToolRegistry:
    """
    Enterprise Tool Registry for registering, inspecting, and invoking tools dynamically.
    """
    def __init__(self):
        self._tools: Dict[str, AgentToolSpec] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register_class_tool(HttpRequestTool())
        self.register_class_tool(DataTransformTool())
        self.register_class_tool(MathSolverTool())

    def register_tool(self, spec: AgentToolSpec) -> None:
        self._tools[spec.name] = spec

    def register_class_tool(self, tool: BaseAgentTool, timeout_seconds: float = 30.0) -> None:
        spec = AgentToolSpec(
            name=tool.name,
            description=tool.description,
            parameters_schema=tool.parameters_schema,
            handler=tool.run,
            timeout_seconds=timeout_seconds
        )
        self._tools[tool.name] = spec

    def get_tool(self, tool_name: str) -> Optional[AgentToolSpec]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[AgentToolSpec]:
        return list(self._tools.values())

agent_tool_registry = ToolRegistry()
