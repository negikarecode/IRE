import ast
from typing import Dict, Any
from app.rules.plugins import rule_plugin_manager

class SafeRuleSandbox:
    """
    Secure Production Rule Execution Sandbox evaluating conditions safely via AST.
    Prevents unauthorized imports, dunder introspection, and system calls.
    """
    ALLOWED_NODES = {
        ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
        ast.Name, ast.Load, ast.Constant, ast.Attribute, ast.And, ast.Or,
        ast.Not, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.In, ast.NotIn, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
        ast.Call, ast.keyword, ast.Subscript, ast.Slice, ast.Dict, ast.List,
        ast.Set, ast.Tuple
    }

    FORBIDDEN_ATTRIBUTES = {
        "__class__", "__bases__", "__subclasses__", "__globals__",
        "__code__", "__dict__", "__import__", "mro"
    }

    def validate_ast(self, condition: str) -> ast.Expression:
        try:
            tree = ast.parse(condition.strip(), mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid rule condition syntax: {str(e)}")

        for node in ast.walk(tree):
            if type(node) not in self.ALLOWED_NODES:
                raise ValueError(f"Forbidden syntax in rule condition: '{type(node).__name__}'")
            
            # Check attribute security
            if isinstance(node, ast.Attribute):
                if node.attr in self.FORBIDDEN_ATTRIBUTES or node.attr.startswith("__"):
                    raise ValueError(f"Security violation: Introspection attribute '{node.attr}' is forbidden.")

            # Check function call security
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name not in rule_plugin_manager.get_functions():
                        raise ValueError(f"Forbidden or unregistered function call: '{func_name}'")

        return tree

    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        tree = self.validate_ast(condition)
        compiled_code = compile(tree, filename="<rule_sandbox>", mode="eval")

        # Global namespace restricted purely to registered plugin functions
        eval_globals = {"__builtins__": {}}
        eval_globals.update(rule_plugin_manager.get_functions())

        # Local namespace containing payload context
        eval_locals = {
            "payload": context,
            "context": context,
            "True": True,
            "False": False,
            "None": None
        }

        result = eval(compiled_code, eval_globals, eval_locals)
        return bool(result)

safe_sandbox = SafeRuleSandbox()
