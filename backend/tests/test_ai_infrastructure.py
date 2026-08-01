import pytest
import asyncio

from app.ai.guardrails import domain_guardrail, DomainPolicyViolationException
from app.ai.model_registry import model_registry, ModelProvider
from app.ai.llm_gateway import llm_gateway, LLMRequest, LLMMessage
from app.ai.prompt_manager import prompt_manager, PromptTemplate
from app.ai.embedding_service import embedding_service
from app.ai.vector_store import vector_store, VectorRecord
from app.ai.conversation_memory import conversation_memory_manager
from app.ai.caching import ai_cache
from app.ai.retry_pipeline import retry_pipeline, CircuitBreaker
from app.ai.evaluator import ai_evaluator
from app.ai.agent_framework import AIAgentFramework

def run_async(coro):
    return asyncio.run(coro)

# 1. Test Domain Guardrails (No medical prompts, No insurance prompts)
def test_domain_guardrail_medical_rejection():
    medical_prompt = "What is the diagnosis and medication prescription for a patient with fever?"
    with pytest.raises(DomainPolicyViolationException) as exc_info:
        domain_guardrail.enforce_policy(medical_prompt, "Test Prompt")
    assert "Medical domain content detected" in str(exc_info.value)

def test_domain_guardrail_insurance_rejection():
    insurance_prompt = "Process the insurance claim and check policy deductible."
    with pytest.raises(DomainPolicyViolationException) as exc_info:
        domain_guardrail.enforce_policy(insurance_prompt, "Test Prompt")
    assert "Insurance domain content detected" in str(exc_info.value)

def test_domain_guardrail_generic_allowed():
    generic_prompt = "Synthesize the step-by-step logical solution for linear regression."
    domain_guardrail.enforce_policy(generic_prompt, "Generic Prompt")

# 2. Test Model Registry (OpenAI, Gemini, Claude, Local)
def test_model_registry_providers():
    openai_models = model_registry.list_by_provider(ModelProvider.OPENAI)
    gemini_models = model_registry.list_by_provider(ModelProvider.GEMINI)
    claude_models = model_registry.list_by_provider(ModelProvider.CLAUDE)
    
    assert len(openai_models) >= 2
    assert len(gemini_models) >= 2
    assert len(claude_models) >= 2
    
    gpt4o = model_registry.get("gpt-4o")
    assert gpt4o is not None
    assert gpt4o.supports_streaming is True
    assert gpt4o.context_window == 128000

# 3. Test LLM Gateway Multi-Provider Generation & Fallback Routing
def test_llm_gateway_providers():
    async def _test():
        # OpenAI Provider
        req_openai = LLMRequest(
            messages=[LLMMessage(role="user", content="Explain quantum computing principles.")],
            primary_model="gpt-4o"
        )
        res_openai = await llm_gateway.generate(req_openai)
        assert res_openai.provider_used == "openai"
        assert "OpenAI Adapter" in res_openai.content

        # Gemini Provider
        req_gemini = LLMRequest(
            messages=[LLMMessage(role="user", content="Summarize solar system dynamics.")],
            primary_model="gemini-1.5-pro"
        )
        res_gemini = await llm_gateway.generate(req_gemini)
        assert res_gemini.provider_used == "gemini"
        assert "Gemini Adapter" in res_gemini.content

        # Claude Provider
        req_claude = LLMRequest(
            messages=[LLMMessage(role="user", content="Write a python Fibonacci algorithm.")],
            primary_model="claude-3-5-sonnet"
        )
        res_claude = await llm_gateway.generate(req_claude)
        assert res_claude.provider_used == "claude"
        assert "Claude Adapter" in res_claude.content

    run_async(_test())

# 4. Test Streaming
def test_llm_gateway_streaming():
    async def _test():
        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Stream step by step execution.")],
            primary_model="gpt-4o"
        )
        chunks = []
        async for chunk in llm_gateway.stream_generate(req):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert chunks[-1].is_final is True

    run_async(_test())

# 5. Test Prompt Registry
def test_prompt_registry():
    async def _test():
        # Render default generic reasoning prompt
        rendered = prompt_manager.render("generic_reasoning", "1.0.0", {
            "context": "System metrics show 99.9% uptime.",
            "query": "What is the stability score?"
        })
        assert "System metrics show 99.9% uptime." in rendered["user_prompt"]

        # Register custom non-domain prompt
        new_template = PromptTemplate(
            template_id="custom_code_reviewer",
            version="1.0.0",
            name="Code Reviewer",
            system_prompt="You are a senior software architect conducting code review.",
            user_prompt_template="Review code snippet:\n{code}",
            variables=["code"]
        )
        prompt_manager.register(new_template)
        
        res = prompt_manager.render("custom_code_reviewer", "1.0.0", {"code": "def foo(): pass"})
        assert "def foo(): pass" in res["user_prompt"]

        # Rejection when registering prompt with medical instruction
        with pytest.raises(DomainPolicyViolationException):
            prompt_manager.register(PromptTemplate(
                template_id="bad_medical",
                version="1.0.0",
                system_prompt="Assist doctors in patient diagnosis.",
                user_prompt_template="{input}"
            ))

    run_async(_test())

# 6. Test Embedding Service (Multi-Provider)
def test_embedding_service():
    async def _test():
        vec_openai = await embedding_service.embed_query("Data science pipeline", provider="openai")
        vec_gemini = await embedding_service.embed_query("Data science pipeline", provider="gemini")
        vec_local = await embedding_service.embed_query("Data science pipeline", provider="local")

        assert len(vec_openai) == 1536
        assert len(vec_gemini) == 1536
        assert len(vec_local) == 1536

        doc_vectors = await embedding_service.embed_documents(["Text 1", "Text 2"], provider="openai")
        assert len(doc_vectors) == 2

    run_async(_test())

# 7. Test Vector Database
def test_vector_store():
    async def _test():
        # Upsert records
        vec1 = await embedding_service.embed_query("Graph theory algorithms")
        vec2 = await embedding_service.embed_query("Database index optimization")

        record1 = VectorRecord(id="rec_1", vector=vec1, payload={"topic": "graphs"}, tenant_id="tenant_a")
        record2 = VectorRecord(id="rec_2", vector=vec2, payload={"topic": "databases"}, tenant_id="tenant_a")

        await vector_store.upsert([record1, record2], collection_name="test_col")

        # Search similarity
        query_v = await embedding_service.embed_query("Graph algorithms")
        search_res = await vector_store.search(query_v, tenant_id="tenant_a", collection_name="test_col", top_k=1)
        
        assert len(search_res) == 1
        assert search_res[0].id == "rec_1"
        assert search_res[0].payload["topic"] == "graphs"

    run_async(_test())

# 8. Test Conversation Memory
def test_conversation_memory():
    async def _test():
        mem = conversation_memory_manager.get_or_create(session_id="sess_test_101", tenant_id="tenant_x", memory_type="sliding")
        mem.clear()
        
        mem.add_turn("user", "Hello assistant")
        mem.add_turn("assistant", "Hello! How can I assist you with technology architecture?")

        history = mem.get_history()
        assert len(history) == 2
        assert history[0].content == "Hello assistant"

    run_async(_test())

# 9. Test Caching (Exact & Semantic)
def test_ai_caching():
    async def _test():
        ai_cache.clear()
        prompt = "Explain matrix multiplication in linear algebra."
        
        # Cache miss initially
        cached = await ai_cache.get_semantic("tenant_c", prompt, "gpt-4o")
        assert cached is None

        # Set cache
        await ai_cache.set_semantic("tenant_c", prompt, "gpt-4o", "Matrix multiplication combines rows and columns.")

        # Cache hit
        hit = await ai_cache.get_semantic("tenant_c", prompt, "gpt-4o")
        assert hit == "Matrix multiplication combines rows and columns."

        stats = ai_cache.get_stats()
        assert stats["hits"] == 1

    run_async(_test())

# 10. Test Retry Pipeline & Circuit Breaker
def test_retry_pipeline():
    async def _test():
        cb = CircuitBreaker(failure_threshold=2)
        p = retry_pipeline
        p.circuit_breaker = cb

        attempts = 0
        async def flaky_func():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise RuntimeError("Transient API Error")
            return "Success"

        result = await p.execute(flaky_func)
        assert result == "Success"
        assert attempts == 2

    run_async(_test())

# 11. Test Evaluation Framework
def test_evaluation_framework():
    async def _test():
        prompt = "How does HTTP/3 improve web request performance?"
        response = "HTTP/3 uses QUIC protocol over UDP to reduce latency and eliminate head-of-line blocking."
        
        report = await ai_evaluator.evaluate_response(prompt, response)
        assert report.passed is True
        assert report.overall_score >= 0.7
        assert "domain_compliance" in report.metrics

    run_async(_test())

# 12. Test Autonomous Agent Framework Integration
def test_agent_framework_execution():
    async def _test():
        agent = AIAgentFramework(agent_id="test_tech_agent", primary_model="gpt-4o")
        result = await agent.run(
            tenant_id="tenant_demo",
            prompt="Synthesize best practices for microservice resilience design patterns."
        )

        assert result.agent_id == "test_tech_agent"
        assert result.confidence_score > 0.0
        assert result.requires_hitl is False

    run_async(_test())
