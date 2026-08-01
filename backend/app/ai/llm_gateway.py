from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, AsyncGenerator
import time
import asyncio
from app.ai.model_registry import ModelProvider, model_registry
from app.ai.guardrails import domain_guardrail, DomainPolicyViolationException

@dataclass
class LLMMessage:
    role: str  # system, user, assistant, tool
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

@dataclass
class LLMRequest:
    messages: List[LLMMessage]
    primary_model: str = "gpt-4o"
    fallback_models: List[str] = field(default_factory=lambda: ["gemini-1.5-pro", "claude-3-5-sonnet", "llama3:70b"])
    temperature: float = 0.2
    max_tokens: int = 2048
    tools: Optional[List[Dict[str, Any]]] = None
    tenant_id: Optional[str] = "default"

@dataclass
class LLMResponse:
    content: str
    model_used: str
    provider_used: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    tool_calls: Optional[List[Dict[str, Any]]] = None
    raw_response: Optional[Dict[str, Any]] = None

@dataclass
class StreamChunk:
    delta: str
    model_used: str
    provider_used: str
    is_final: bool = False
    finish_reason: Optional[str] = None

class ILLMProviderAdapter(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest, model_id: str) -> LLMResponse:
        pass

    @abstractmethod
    async def stream_generate(self, request: LLMRequest, model_id: str) -> AsyncGenerator[StreamChunk, None]:
        pass

class OpenAIAdapter(ILLMProviderAdapter):
    """
    Provider-independent adapter for OpenAI LLMs (GPT-4o, GPT-4o-mini, O1).
    """
    async def generate(self, request: LLMRequest, model_id: str) -> LLMResponse:
        start_time = time.time()
        # Extract user prompt for synthesis response
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        latency = (time.time() - start_time) * 1000
        output_text = f"[OpenAI Adapter] Generated response for model '{model_id}' based on: {prompt_text[:80]}..."
        
        return LLMResponse(
            content=output_text,
            model_used=model_id,
            provider_used=ModelProvider.OPENAI.value,
            input_tokens=len(str(request.messages)) // 4,
            output_tokens=len(output_text) // 4,
            latency_ms=latency
        )

    async def stream_generate(self, request: LLMRequest, model_id: str) -> AsyncGenerator[StreamChunk, None]:
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        tokens = [f"[OpenAI Stream - {model_id}] ", "Processing query: ", prompt_text[:40], "... ", "Execution complete."]
        
        for i, token in enumerate(tokens):
            await asyncio.sleep(0.02)
            is_last = (i == len(tokens) - 1)
            yield StreamChunk(
                delta=token,
                model_used=model_id,
                provider_used=ModelProvider.OPENAI.value,
                is_final=is_last,
                finish_reason="stop" if is_last else None
            )

class GeminiAdapter(ILLMProviderAdapter):
    """
    Provider-independent adapter for Google Gemini LLMs (Gemini 1.5 Pro, Flash, Gemini 2.0).
    """
    async def generate(self, request: LLMRequest, model_id: str) -> LLMResponse:
        start_time = time.time()
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        latency = (time.time() - start_time) * 1000
        output_text = f"[Gemini Adapter] Synthesized intelligence from model '{model_id}' for query: {prompt_text[:80]}..."
        
        return LLMResponse(
            content=output_text,
            model_used=model_id,
            provider_used=ModelProvider.GEMINI.value,
            input_tokens=len(str(request.messages)) // 4,
            output_tokens=len(output_text) // 4,
            latency_ms=latency
        )

    async def stream_generate(self, request: LLMRequest, model_id: str) -> AsyncGenerator[StreamChunk, None]:
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        tokens = [f"[Gemini Stream - {model_id}] ", "Received request: ", prompt_text[:40], "... ", "Streaming complete."]
        
        for i, token in enumerate(tokens):
            await asyncio.sleep(0.02)
            is_last = (i == len(tokens) - 1)
            yield StreamChunk(
                delta=token,
                model_used=model_id,
                provider_used=ModelProvider.GEMINI.value,
                is_final=is_last,
                finish_reason="stop" if is_last else None
            )

class ClaudeAdapter(ILLMProviderAdapter):
    """
    Provider-independent adapter for Anthropic Claude LLMs (Claude 3.5 Sonnet, Claude 3 Haiku).
    """
    async def generate(self, request: LLMRequest, model_id: str) -> LLMResponse:
        start_time = time.time()
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        latency = (time.time() - start_time) * 1000
        output_text = f"[Claude Adapter] Formulated response via Anthropic '{model_id}' for query: {prompt_text[:80]}..."
        
        return LLMResponse(
            content=output_text,
            model_used=model_id,
            provider_used=ModelProvider.CLAUDE.value,
            input_tokens=len(str(request.messages)) // 4,
            output_tokens=len(output_text) // 4,
            latency_ms=latency
        )

    async def stream_generate(self, request: LLMRequest, model_id: str) -> AsyncGenerator[StreamChunk, None]:
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        tokens = [f"[Claude Stream - {model_id}] ", "Analyzing input: ", prompt_text[:40], "... ", "Synthesis complete."]
        
        for i, token in enumerate(tokens):
            await asyncio.sleep(0.02)
            is_last = (i == len(tokens) - 1)
            yield StreamChunk(
                delta=token,
                model_used=model_id,
                provider_used=ModelProvider.CLAUDE.value,
                is_final=is_last,
                finish_reason="stop" if is_last else None
            )

class LocalModelAdapter(ILLMProviderAdapter):
    """
    Provider-independent adapter for Local Open Source LLMs (Ollama, vLLM).
    """
    async def generate(self, request: LLMRequest, model_id: str) -> LLMResponse:
        start_time = time.time()
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        latency = (time.time() - start_time) * 1000
        output_text = f"[Local Model Adapter] Executed local inference for model '{model_id}' on query: {prompt_text[:80]}..."
        
        return LLMResponse(
            content=output_text,
            model_used=model_id,
            provider_used="local",
            input_tokens=len(str(request.messages)) // 4,
            output_tokens=len(output_text) // 4,
            latency_ms=latency
        )

    async def stream_generate(self, request: LLMRequest, model_id: str) -> AsyncGenerator[StreamChunk, None]:
        prompt_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        tokens = [f"[Local Stream - {model_id}] ", "Local execution: ", prompt_text[:40], "... ", "Done."]
        
        for i, token in enumerate(tokens):
            await asyncio.sleep(0.02)
            is_last = (i == len(tokens) - 1)
            yield StreamChunk(
                delta=token,
                model_used=model_id,
                provider_used="local",
                is_final=is_last,
                finish_reason="stop" if is_last else None
            )

class LLMGateway:
    """
    Provider-Independent LLM Gateway featuring multi-provider routing,
    fallback chains, streaming support, and domain guardrail enforcement.
    """
    def __init__(self):
        self._adapters: Dict[ModelProvider, ILLMProviderAdapter] = {
            ModelProvider.OPENAI: OpenAIAdapter(),
            ModelProvider.GEMINI: GeminiAdapter(),
            ModelProvider.CLAUDE: ClaudeAdapter(),
            ModelProvider.LOCAL_OLLAMA: LocalModelAdapter(),
            ModelProvider.LOCAL_VLLM: LocalModelAdapter()
        }

    def _validate_request(self, request: LLMRequest) -> None:
        """
        Enforce strict domain policy guardrails:
        No medical prompts & No insurance prompts allowed anywhere in request messages.
        """
        for idx, msg in enumerate(request.messages):
            domain_guardrail.enforce_policy(msg.content, context_name=f"Message[{idx}] ({msg.role})")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self._validate_request(request)

        candidate_models = [request.primary_model] + [m for m in request.fallback_models if m != request.primary_model]
        errors = []

        for model_id in candidate_models:
            meta = model_registry.get(model_id)
            if not meta:
                continue

            adapter = self._adapters.get(meta.provider)
            if not adapter:
                continue

            try:
                return await adapter.generate(request, model_id)
            except Exception as e:
                errors.append(f"Model '{model_id}' failed: {str(e)}")

        raise RuntimeError(f"All LLM Gateway candidate models failed. Exhausted candidates: {errors}")

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[StreamChunk, None]:
        self._validate_request(request)

        candidate_models = [request.primary_model] + [m for m in request.fallback_models if m != request.primary_model]
        
        for model_id in candidate_models:
            meta = model_registry.get(model_id)
            if not meta:
                continue

            adapter = self._adapters.get(meta.provider)
            if not adapter:
                continue

            try:
                async for chunk in adapter.stream_generate(request, model_id):
                    yield chunk
                return
            except Exception:
                continue

        raise RuntimeError("All LLM Gateway streaming candidates failed.")

llm_gateway = LLMGateway()
