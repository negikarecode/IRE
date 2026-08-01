from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class ModelProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    LOCAL_OLLAMA = "local_ollama"
    LOCAL_VLLM = "local_vllm"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"

@dataclass
class ModelMetadata:
    model_id: str
    provider: ModelProvider
    context_window: int
    supports_tools: bool
    supports_vision: bool
    supports_streaming: bool = True
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    description: str = ""

class ModelRegistry:
    """
    Central provider-independent Model Registry managing capabilities,
    fallback orders, context lengths, token costs, and feature flags.
    """
    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._register_default_models()

    def _register_default_models(self):
        # OpenAI Models
        self.register(ModelMetadata(
            model_id="gpt-4o",
            provider=ModelProvider.OPENAI,
            context_window=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.005,
            cost_per_1k_output_tokens=0.015,
            description="OpenAI flagship multimodal reasoning model"
        ))
        self.register(ModelMetadata(
            model_id="gpt-4o-mini",
            provider=ModelProvider.OPENAI,
            context_window=128000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.00015,
            cost_per_1k_output_tokens=0.0006,
            description="Fast, lightweight OpenAI model for high-throughput tasks"
        ))
        self.register(ModelMetadata(
            model_id="o1-mini",
            provider=ModelProvider.OPENAI,
            context_window=128000,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.012,
            description="OpenAI reasoning model for complex logical synthesis"
        ))

        # Gemini Models
        self.register(ModelMetadata(
            model_id="gemini-1.5-pro",
            provider=ModelProvider.GEMINI,
            context_window=1000000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.0035,
            cost_per_1k_output_tokens=0.0105,
            description="Google Gemini long-context flagship model"
        ))
        self.register(ModelMetadata(
            model_id="gemini-1.5-flash",
            provider=ModelProvider.GEMINI,
            context_window=1000000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.00035,
            cost_per_1k_output_tokens=0.00105,
            description="Google Gemini high-speed, low-latency model"
        ))
        self.register(ModelMetadata(
            model_id="gemini-2.0-flash",
            provider=ModelProvider.GEMINI,
            context_window=1000000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.0001,
            cost_per_1k_output_tokens=0.0004,
            description="Next-gen ultra-fast Gemini model"
        ))

        # Claude Models
        self.register(ModelMetadata(
            model_id="claude-3-5-sonnet",
            provider=ModelProvider.CLAUDE,
            context_window=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015,
            description="Anthropic Claude state-of-the-art intelligence model"
        ))
        self.register(ModelMetadata(
            model_id="claude-3-haiku",
            provider=ModelProvider.CLAUDE,
            context_window=200000,
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.00025,
            cost_per_1k_output_tokens=0.00125,
            description="Anthropic Claude fast and affordable model"
        ))

        # Local Open Source Models (Ollama / vLLM)
        self.register(ModelMetadata(
            model_id="llama3:70b",
            provider=ModelProvider.LOCAL_OLLAMA,
            context_window=8192,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.0,
            cost_per_1k_output_tokens=0.0,
            description="Meta Llama 3 70B hosted locally via Ollama"
        ))
        self.register(ModelMetadata(
            model_id="mistral-large-vllm",
            provider=ModelProvider.LOCAL_VLLM,
            context_window=32768,
            supports_tools=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.0,
            cost_per_1k_output_tokens=0.0,
            description="Mistral Large served via local vLLM endpoint"
        ))

    def register(self, metadata: ModelMetadata) -> None:
        self._models[metadata.model_id] = metadata

    def unregister(self, model_id: str) -> bool:
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def get(self, model_id: str) -> Optional[ModelMetadata]:
        return self._models.get(model_id)

    def list_all(self) -> List[ModelMetadata]:
        return list(self._models.values())

    def list_by_provider(self, provider: ModelProvider) -> List[ModelMetadata]:
        return [m for m in self._models.values() if m.provider == provider]

    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        model = self.get(model_id)
        if not model:
            return 0.0
        input_cost = (input_tokens / 1000.0) * model.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000.0) * model.cost_per_1k_output_tokens
        return round(input_cost + output_cost, 6)

model_registry = ModelRegistry()
