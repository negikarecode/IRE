"""
AI Infrastructure Framework Package
Provides LLM Gateway (OpenAI, Gemini, Claude, Local), Prompt Registry, Model Registry,
Embedding Service, Vector Database, Conversation Memory, Caching, Retry Pipeline,
Streaming, Evaluation Framework, and Domain Policy Guardrails (No medical prompts, No insurance prompts).
"""

from app.ai.guardrails import domain_guardrail, DomainGuardrail, DomainPolicyViolationException
from app.ai.model_registry import model_registry, ModelRegistry, ModelProvider, ModelMetadata
from app.ai.llm_gateway import llm_gateway, LLMGateway, LLMRequest, LLMResponse, LLMMessage, StreamChunk
from app.ai.prompt_manager import prompt_manager, PromptManager, PromptTemplate
from app.ai.embedding_service import embedding_service, MultiProviderEmbeddingService
from app.ai.vector_store import vector_store, InMemoryVectorStore, VectorRecord, SearchResult, CollectionMetadata
from app.ai.conversation_memory import conversation_memory_manager, ConversationMemoryManager, SlidingWindowMemory, SummaryConversationMemory, VectorBackedLongTermMemory
from app.ai.caching import ai_cache, AICacheManager
from app.ai.retry_pipeline import retry_pipeline, RetryPipeline, CircuitBreaker
from app.ai.evaluator import ai_evaluator, AIEvaluationFramework, EvaluationReport, MetricResult
from app.ai.agent_framework import AIAgentFramework, AgentExecutionResult

__all__ = [
    "domain_guardrail",
    "DomainGuardrail",
    "DomainPolicyViolationException",
    "model_registry",
    "ModelRegistry",
    "ModelProvider",
    "ModelMetadata",
    "llm_gateway",
    "LLMGateway",
    "LLMRequest",
    "LLMResponse",
    "LLMMessage",
    "StreamChunk",
    "prompt_manager",
    "PromptManager",
    "PromptTemplate",
    "embedding_service",
    "MultiProviderEmbeddingService",
    "vector_store",
    "InMemoryVectorStore",
    "VectorRecord",
    "SearchResult",
    "CollectionMetadata",
    "conversation_memory_manager",
    "ConversationMemoryManager",
    "SlidingWindowMemory",
    "SummaryConversationMemory",
    "VectorBackedLongTermMemory",
    "ai_cache",
    "AICacheManager",
    "retry_pipeline",
    "RetryPipeline",
    "CircuitBreaker",
    "ai_evaluator",
    "AIEvaluationFramework",
    "EvaluationReport",
    "MetricResult",
    "AIAgentFramework",
    "AgentExecutionResult",
]
