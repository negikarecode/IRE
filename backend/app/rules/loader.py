import json
import os
from typing import List, Dict, Any, Union
from app.rules.schema import DeclarativeRule, RuleSeverity, RuleAction
from app.rules.registry import rule_registry

class RuleLoader:
    """
    Production Rule Loader.
    Dynamically imports rule definitions from JSON strings, dictionary structures,
    YAML payloads, or files without requiring code changes or backend deployments.
    """
    def parse_rule_dict(self, item: Dict[str, Any]) -> DeclarativeRule:
        actions = []
        for a in item.get("actions", []):
            actions.append(RuleAction(
                action_type=a["action_type"],
                params=a.get("params", {})
            ))

        return DeclarativeRule(
            rule_id=item["rule_id"],
            name=item["name"],
            version=item.get("version", "1.0.0"),
            group=item.get("group", "default"),
            priority=item.get("priority", 100),
            condition=item["condition"],
            severity=RuleSeverity(item.get("severity", "WARNING")),
            explanation=item.get("explanation", ""),
            suggestion=item.get("suggestion", ""),
            actions=actions,
            dependencies=item.get("dependencies", []),
            is_active=item.get("is_active", True),
            tags=item.get("tags", [])
        )

    def load_from_json_string(self, json_content: str) -> List[DeclarativeRule]:
        data = json.loads(json_content)
        rule_list = data if isinstance(data, list) else [data]
        loaded_rules = []

        for item in rule_list:
            rule = self.parse_rule_dict(item)
            rule_registry.register(rule)
            loaded_rules.append(rule)

        return loaded_rules

    def load_from_file(self, filepath: str) -> List[DeclarativeRule]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Rule file not found at path: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if filepath.endswith(".json"):
            return self.load_from_json_string(content)
        else:
            # Fallback JSON loader for raw text definitions
            return self.load_from_json_string(content)

rule_loader = RuleLoader()
