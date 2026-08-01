import pytest
import asyncio

from app.sdk import (
    BaseRulePlugin,
    BaseValidatorPlugin,
    BaseRiskEnginePlugin,
    BasePolicyProviderPlugin,
    BaseMedicalExtractorPlugin,
    BaseReasoningPipelinePlugin,
    BaseAgentPlugin,
    BaseAppealEnginePlugin,
    BasePackageValidatorPlugin,
    register_rule,
    register_validator,
    register_risk_engine,
    register_policy_provider,
    register_medical_extractor,
    register_reasoning_pipeline,
    register_agent,
    register_appeal_engine,
    register_package_validator,
    plugin_registry,
    plugin_discovery_engine
)

def run_async(coro):
    return asyncio.run(coro)

# 1. Test All 9 Extension Points Registration & Execution
def test_all_9_extension_points():
    async def _test():
        # 1. Rule
        @register_rule("test_rule_1", "Test Rule Plugin")
        class Rule1(BaseRulePlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def evaluate_rule(self, context): return {"rule_passed": context.get("score", 0) > 50}

        # 2. Validator
        @register_validator("test_val_1", "Test Validator Plugin")
        class Val1(BaseValidatorPlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def validate_payload(self, data): return {"valid": "id" in data}

        # 3. Risk Engine
        @register_risk_engine("test_risk_1", "Test Risk Engine Plugin")
        class Risk1(BaseRiskEnginePlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def calculate_risk(self, entity_data): return {"score": 0.25}

        # 4. Policy Provider
        @register_policy_provider("test_policy_1", "Test Policy Provider Plugin")
        class Policy1(BasePolicyProviderPlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def fetch_policy(self, policy_id, context): return {"policy": "ACTIVE"}

        # 5. Medical Extractor
        @register_medical_extractor("test_med_1", "Test Medical Extractor Plugin")
        class Med1(BaseMedicalExtractorPlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def extract_clinical_entities(self, text_content): return {"codes": ["E11.9"]}

        # 6. Reasoning Pipeline
        @register_reasoning_pipeline("test_reason_1", "Test Reasoning Pipeline Plugin")
        class Reason1(BaseReasoningPipelinePlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def run_pipeline(self, input_data): return {"status": "FINISHED"}

        # 7. AI Agent
        @register_agent("test_agent_1", "Test AI Agent Plugin")
        class Agent1(BaseAgentPlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def execute_task(self, goal, context): return {"summary": "Done"}

        # 8. Appeal Engine
        @register_appeal_engine("test_appeal_1", "Test Appeal Engine Plugin")
        class Appeal1(BaseAppealEnginePlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def process_appeal(self, appeal_case): return {"decision": "OVERTURNED"}

        # 9. Package Validator
        @register_package_validator("test_pkg_1", "Test Package Validator Plugin")
        class Pkg1(BasePackageValidatorPlugin):
            async def initialize(self) -> bool: return True
            async def shutdown(self) -> None: pass
            async def validate_package_manifest(self, manifest): return {"valid_pkg": True}

        # Execute tests across all 9 extension points
        r1 = await plugin_registry.execute("rules", "test_rule_1", "evaluate_rule", {"score": 80})
        assert r1["rule_passed"] is True

        r2 = await plugin_registry.execute("validators", "test_val_1", "validate_payload", {"id": "123"})
        assert r2["valid"] is True

        r3 = await plugin_registry.execute("risk_engines", "test_risk_1", "calculate_risk", {})
        assert r3["score"] == 0.25

        r4 = await plugin_registry.execute("policy_providers", "test_policy_1", "fetch_policy", "p123", {})
        assert r4["policy"] == "ACTIVE"

        r5 = await plugin_registry.execute("medical_extractors", "test_med_1", "extract_clinical_entities", "text")
        assert "E11.9" in r5["codes"]

        r6 = await plugin_registry.execute("reasoning_pipelines", "test_reason_1", "run_pipeline", {})
        assert r6["status"] == "FINISHED"

        r7 = await plugin_registry.execute("agents", "test_agent_1", "execute_task", "goal", {})
        assert r7["summary"] == "Done"

        r8 = await plugin_registry.execute("appeal_engines", "test_appeal_1", "process_appeal", {})
        assert r8["decision"] == "OVERTURNED"

        r9 = await plugin_registry.execute("package_validators", "test_pkg_1", "validate_package_manifest", {})
        assert r9["valid_pkg"] is True

    run_async(_test())

# 2. Test Automatic Plugin Discovery Engine
def test_automatic_plugin_discovery():
    discovery_res = plugin_discovery_engine.discover_and_load()
    assert discovery_res["status"] == "DISCOVERY_COMPLETE"
    assert discovery_res["registered_plugins_count"] >= 9
