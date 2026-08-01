from abc import abstractmethod
from typing import Dict, Any, List, Optional
from app.sdk.base import BasePlugin

# 1. Rules Extension Point
class BaseRulePlugin(BasePlugin):
    """Extension Point 1: Custom Rule Evaluator Plugin."""
    @abstractmethod
    async def evaluate_rule(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates rule logic against provided context."""
        pass

# 2. Validators Extension Point
class BaseValidatorPlugin(BasePlugin):
    """Extension Point 2: Custom Data & Payload Validator Plugin."""
    @abstractmethod
    async def validate_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validates incoming business data payload."""
        pass

# 3. Risk Engines Extension Point
class BaseRiskEnginePlugin(BasePlugin):
    """Extension Point 3: Custom Business Risk Scoring Engine Plugin."""
    @abstractmethod
    async def calculate_risk(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates risk score (0.0 to 1.0) and risk factors."""
        pass

# 4. Policy Providers Extension Point
class BasePolicyProviderPlugin(BasePlugin):
    """Extension Point 4: Custom Enterprise Policy Provider Plugin."""
    @abstractmethod
    async def fetch_policy(self, policy_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches policy rules and compliance terms."""
        pass

# 5. Medical Extractors Extension Point
class BaseMedicalExtractorPlugin(BasePlugin):
    """Extension Point 5: Custom Medical / Clinical Entity Extractor Plugin."""
    @abstractmethod
    async def extract_clinical_entities(self, text_content: str) -> Dict[str, Any]:
        """Extracts clinical entities, diagnoses, or procedure codes."""
        pass

# 6. Reasoning Pipelines Extension Point
class BaseReasoningPipelinePlugin(BasePlugin):
    """Extension Point 6: Custom Multi-Stage Reasoning Pipeline Plugin."""
    @abstractmethod
    async def run_pipeline(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes multi-stage reasoning pipeline."""
        pass

# 7. AI Agents Extension Point
class BaseAgentPlugin(BasePlugin):
    """Extension Point 7: Custom Autonomous AI Agent Plugin."""
    @abstractmethod
    async def execute_task(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes autonomous agent task."""
        pass

# 8. Appeal Engines Extension Point
class BaseAppealEnginePlugin(BasePlugin):
    """Extension Point 8: Custom Appeal Case Engine Plugin."""
    @abstractmethod
    async def process_appeal(self, appeal_case: Dict[str, Any]) -> Dict[str, Any]:
        """Processes customer / partner appeal case."""
        pass

# 9. Package Validators Extension Point
class BasePackageValidatorPlugin(BasePlugin):
    """Extension Point 9: Custom Package Manifest Validator Plugin."""
    @abstractmethod
    async def validate_package_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Validates release package manifest structure."""
        pass
