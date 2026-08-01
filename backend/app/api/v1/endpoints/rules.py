from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.core.dependencies import get_tenant_header
from app.rules.schema import DeclarativeRule, RuleSeverity, RuleAction
from app.rules.registry import rule_registry
from app.rules.executor import rule_executor
from app.rules.loader import rule_loader
from app.rules.testing import rule_testing_suite, RuleTestCase
from app.rules.metrics import rule_metrics
from app.rules.caching import rule_cache
from app.rules.marketplace import rule_marketplace
from app.ai.guardrails import DomainPolicyViolationException

router = APIRouter()

class RuleActionDTO(BaseModel):
    action_type: str
    params: Dict[str, Any] = {}

class RuleCreateDTO(BaseModel):
    rule_id: str
    name: str
    version: str = "1.0.0"
    group: str = "default"
    priority: int = 100
    condition: str
    severity: RuleSeverity = RuleSeverity.WARNING
    explanation: str = ""
    suggestion: str = ""
    actions: List[RuleActionDTO] = []
    dependencies: List[str] = []
    tags: List[str] = []
    is_active: bool = True

class RuleExecuteDTO(BaseModel):
    context_id: str
    group: Optional[str] = None
    payload: Dict[str, Any]

class RuleTestDTO(BaseModel):
    rule: RuleCreateDTO
    test_cases: List[Dict[str, Any]]

class BatchLoadDTO(BaseModel):
    json_content: str

from app.core.exceptions import BadRequestException, NotFoundException

@router.post("/execute", status_code=status.HTTP_200_OK)
async def execute_rules(
    body: RuleExecuteDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    try:
        report = await rule_executor.execute(
            tenant_id=tenant_id,
            context_id=body.context_id,
            context_payload=body.payload,
            group=body.group
        )
        return {
            "success": True,
            "message": "Rules executed successfully",
            "data": report
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_rule(dto: RuleCreateDTO):
    try:
        rule = DeclarativeRule(
            rule_id=dto.rule_id,
            name=dto.name,
            version=dto.version,
            group=dto.group,
            priority=dto.priority,
            condition=dto.condition,
            severity=dto.severity,
            explanation=dto.explanation,
            suggestion=dto.suggestion,
            actions=[RuleAction(action_type=a.action_type, params=a.params) for a in dto.actions],
            dependencies=dto.dependencies,
            tags=dto.tags,
            is_active=dto.is_active
        )
        rule_registry.register(rule)
        return {
            "success": True,
            "message": "Rule registered successfully",
            "data": {"status": "REGISTERED", "rule_id": dto.rule_id, "group": dto.group, "version": dto.version}
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

@router.get("/", status_code=status.HTTP_200_OK)
async def list_rules(group: Optional[str] = None, tag: Optional[str] = None, active_only: bool = True):
    rules = rule_registry.list_rules(group=group, tag=tag, active_only=active_only)
    data = [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "version": r.version,
            "group": r.group,
            "priority": r.priority,
            "condition": r.condition,
            "severity": r.severity.value,
            "explanation": r.explanation,
            "suggestion": r.suggestion,
            "actions": [{"action_type": a.action_type, "params": a.params} for a in r.actions],
            "dependencies": r.dependencies,
            "tags": r.tags,
            "is_active": r.is_active
        }
        for r in rules
    ]
    return {
        "success": True,
        "message": "Rules listed successfully",
        "data": data
    }

@router.get("/groups", status_code=status.HTTP_200_OK)
async def list_groups():
    return {
        "success": True,
        "message": "Rule groups retrieved successfully",
        "data": {"groups": rule_registry.list_groups()}
    }

@router.post("/load", status_code=status.HTTP_200_OK)
async def batch_load_rules(dto: BatchLoadDTO):
    try:
        loaded = rule_loader.load_from_json_string(dto.json_content)
        return {
            "success": True,
            "message": "Rules loaded successfully",
            "data": {"status": "loaded", "rules_count": len(loaded)}
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))
    except Exception as e:
        raise BadRequestException(message=f"Failed to load rules: {str(e)}")

@router.post("/test", status_code=status.HTTP_200_OK)
async def test_rule(dto: RuleTestDTO):
    try:
        rule = DeclarativeRule(
            rule_id=dto.rule.rule_id,
            name=dto.rule.name,
            version=dto.rule.version,
            group=dto.rule.group,
            priority=dto.rule.priority,
            condition=dto.rule.condition,
            severity=dto.rule.severity,
            explanation=dto.rule.explanation,
            suggestion=dto.rule.suggestion
        )
        test_cases = [
            RuleTestCase(
                test_id=tc.get("test_id", f"test_{idx}"),
                mock_payload=tc["mock_payload"],
                expected_fired=tc["expected_fired"]
            )
            for idx, tc in enumerate(dto.test_cases)
        ]
        results = rule_testing_suite.run_tests(rule, test_cases)
        return {
            "success": True,
            "message": "Rule testing completed",
            "data": results
        }
    except Exception as e:
        raise BadRequestException(message=str(e))

@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_rule_metrics():
    return {
        "success": True,
        "message": "Rule metrics retrieved successfully",
        "data": {
            "engine_metrics": rule_metrics.get_metrics(),
            "cache_stats": rule_cache.get_stats()
        }
    }

@router.post("/cache/clear", status_code=status.HTTP_200_OK)
async def clear_rule_cache():
    rule_cache.clear()
    return {
        "success": True,
        "message": "Rule cache cleared successfully",
        "data": {"status": "cleared"}
    }

@router.get("/marketplace", status_code=status.HTTP_200_OK)
async def list_marketplace():
    packages = rule_marketplace.list_packages()
    data = [
        {
            "package_id": p.package_id,
            "name": p.name,
            "author": p.author,
            "version": p.version,
            "description": p.description,
            "rule_count": len(p.rules),
            "downloads": p.downloads
        }
        for p in packages
    ]
    return {
        "success": True,
        "message": "Marketplace packages listed successfully",
        "data": data
    }

@router.post("/marketplace/install/{package_id}", status_code=status.HTTP_200_OK)
async def install_marketplace_package(package_id: str):
    installed_rules = rule_marketplace.install_package(package_id)
    return {
        "success": True,
        "message": "Marketplace package installed successfully",
        "data": {"status": "INSTALLED", "installed_count": len(installed_rules)}
    }
