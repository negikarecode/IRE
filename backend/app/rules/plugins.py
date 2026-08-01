from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List, Optional
import re
import datetime

class IRulePlugin(ABC):
    """
    Extension point interface for custom condition functions.
    Allows developers to extend the rule sandbox with custom python functions.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        pass

class IRuleActionHandler(ABC):
    """
    Extension point interface for custom action handlers triggered when rules fire.
    """
    @property
    @abstractmethod
    def action_type(self) -> str:
        pass

    @abstractmethod
    async def handle_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        pass

# Built-in safe plugin functions
class RegexMatchPlugin(IRulePlugin):
    @property
    def name(self) -> str:
        return "regex_match"

    def execute(self, pattern: str, text: str) -> bool:
        if not pattern or not text:
            return False
        return bool(re.search(pattern, str(text)))

class InListPlugin(IRulePlugin):
    @property
    def name(self) -> str:
        return "in_list"

    def execute(self, item: Any, valid_list: List[Any]) -> bool:
        return item in valid_list

class DateDiffDaysPlugin(IRulePlugin):
    @property
    def name(self) -> str:
        return "date_diff_days"

    def execute(self, date_str_1: str, date_str_2: str) -> int:
        try:
            d1 = datetime.date.fromisoformat(str(date_str_1)[:10])
            d2 = datetime.date.fromisoformat(str(date_str_2)[:10])
            return abs((d1 - d2).days)
        except Exception:
            return 0

# Default Action Handlers
class LogAlertActionHandler(IRuleActionHandler):
    @property
    def action_type(self) -> str:
        return "log_alert"

    async def handle_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        msg = params.get("message", "Rule triggered alert log.")
        return {"status": "logged", "message": msg}

class SetFieldActionHandler(IRuleActionHandler):
    @property
    def action_type(self) -> str:
        return "set_field"

    async def handle_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        field_name = params.get("field")
        value = params.get("value")
        if field_name:
            context[field_name] = value
        return {"status": "field_updated", "field": field_name, "value": value}

class RulePluginManager:
    """
    Central Manager for Rule Engine Extension Points (Plugins & Action Handlers).
    Allows external developers to register plugins dynamically without backend code edits.
    """
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._action_handlers: Dict[str, IRuleActionHandler] = {}
        self._register_defaults()

    def _register_defaults(self):
        # Built-in condition functions
        self.register_function("len", len)
        self.register_function("sum", sum)
        self.register_function("min", min)
        self.register_function("max", max)
        self.register_function("abs", abs)
        self.register_function("round", round)
        self.register_plugin(RegexMatchPlugin())
        self.register_plugin(InListPlugin())
        self.register_plugin(DateDiffDaysPlugin())

        # Built-in action handlers
        self.register_action_handler(LogAlertActionHandler())
        self.register_action_handler(SetFieldActionHandler())

    def register_function(self, name: str, func: Callable) -> None:
        self._functions[name] = func

    def register_plugin(self, plugin: IRulePlugin) -> None:
        self._functions[plugin.name] = plugin.execute

    def register_action_handler(self, handler: IRuleActionHandler) -> None:
        self._action_handlers[handler.action_type] = handler

    def get_functions(self) -> Dict[str, Callable]:
        return self._functions

    def get_action_handler(self, action_type: str) -> Optional[IRuleActionHandler]:
        return self._action_handlers.get(action_type)

rule_plugin_manager = RulePluginManager()
