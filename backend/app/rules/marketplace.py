from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.rules.schema import DeclarativeRule
from app.rules.registry import rule_registry

@dataclass
class RuleMarketplacePackage:
    package_id: str
    name: str
    author: str
    version: str
    description: str
    rules: List[DeclarativeRule]
    downloads: int = 0
    rating: float = 5.0

class RuleMarketplaceRegistry:
    """
    Marketplace for discovering, downloading, and publishing reusable rule plugins.
    """
    def __init__(self):
        self._packages: Dict[str, RuleMarketplacePackage] = {}
        self._seed_sample_packages()

    def _seed_sample_packages(self):
        # Sample structural integrity rule package
        sample_rule = DeclarativeRule(
            rule_id="RULE_STRUCT_MISSING_ID",
            name="Missing Payload ID Verification",
            version="1.0.0",
            condition="payload.get('id') is None",
            severity="WARNING",
            explanation="Payload is missing mandatory 'id' identifier attribute.",
            suggestion="Ensure client request includes a valid unique payload identifier.",
            priority=200
        )
        pkg = RuleMarketplacePackage(
            package_id="pkg_structural_integrity",
            name="Structural Payload Integrity Rules",
            author="IRE Core Architecture Team",
            version="1.0.0",
            description="Generic structural payload validation rules.",
            rules=[sample_rule]
        )
        self._packages[pkg.package_id] = pkg

    def publish_package(self, package: RuleMarketplacePackage) -> None:
        self._packages[package.package_id] = package

    def list_packages(self) -> List[RuleMarketplacePackage]:
        return list(self._packages.values())

    def install_package(self, package_id: str) -> List[DeclarativeRule]:
        pkg = self._packages.get(package_id)
        if not pkg:
            raise ValueError(f"Marketplace package '{package_id}' not found.")
        
        pkg.downloads += 1
        for rule in pkg.rules:
            rule_registry.register(rule)
        return pkg.rules

rule_marketplace = RuleMarketplaceRegistry()
