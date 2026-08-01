from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import asyncio

from app.core.dependencies import get_tenant_header
from app.ai.llm_gateway import llm_gateway, LLMRequest, LLMMessage
from app.ai.prompt_manager import prompt_manager, PromptTemplate
from app.ai.model_registry import model_registry
from app.ai.embedding_service import embedding_service
from app.ai.vector_store import vector_store, VectorRecord
from app.ai.conversation_memory import conversation_memory_manager
from app.ai.caching import ai_cache
from app.ai.evaluator import ai_evaluator
from app.ai.guardrails import DomainPolicyViolationException, domain_guardrail

router = APIRouter()

# DTO Schemas
class GenerateRequestDTO(BaseModel):
    prompt: str
    primary_model: str = "gpt-4o"
    fallback_models: List[str] = ["gemini-1.5-pro", "claude-3-5-sonnet", "llama3:70b"]
    system_prompt: Optional[str] = "You are an AI infrastructure reasoning assistant."
    use_cache: bool = True

class GenerateResponseDTO(BaseModel):
    content: str
    model_used: str
    provider_used: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cached: bool = False
    evaluation_score: float

class PromptTemplateDTO(BaseModel):
    template_id: str
    version: str = "1.0.0"
    name: str
    description: str = ""
    system_prompt: str
    user_prompt_template: str
    tags: List[str] = []
    variables: List[str] = []

class RenderPromptDTO(BaseModel):
    template_id: str
    version: str = "1.0.0"
    variables: Dict[str, Any]

class EmbeddingRequestDTO(BaseModel):
    text: Optional[str] = None
    texts: Optional[List[str]] = None
    provider: Optional[str] = "openai"

class VectorUpsertDTO(BaseModel):
    collection_name: str = "default"
    records: List[Dict[str, Any]]

class VectorSearchDTO(BaseModel):
    query: str
    collection_name: str = "default"
    top_k: int = 5
    filter_metadata: Optional[Dict[str, Any]] = None

class AddTurnDTO(BaseModel):
    session_id: str
    role: str
    content: str
    memory_type: str = "sliding"

class EvaluateRequestDTO(BaseModel):
    prompt: str
    response: str
    context: str = ""

# 1. LLM Generation Endpoint
from app.core.exceptions import BadRequestException, NotFoundException

# 1. LLM Generation Endpoint
@router.post("/generate", status_code=200)
async def generate_text(
    body: GenerateRequestDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    try:
        if body.use_cache:
            cached_text = await ai_cache.get_semantic(tenant_id, body.prompt, body.primary_model)
            if cached_text:
                eval_report = await ai_evaluator.evaluate_response(body.prompt, cached_text)
                res = GenerateResponseDTO(
                    content=cached_text,
                    model_used=body.primary_model,
                    provider_used="cache",
                    input_tokens=0,
                    output_tokens=len(cached_text) // 4,
                    latency_ms=1.5,
                    cached=True,
                    evaluation_score=eval_report.overall_score
                )
                return {
                    "success": True,
                    "message": "Text generated from cache",
                    "data": res.model_dump()
                }

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=body.system_prompt),
                LLMMessage(role="user", content=body.prompt)
            ],
            primary_model=body.primary_model,
            fallback_models=body.fallback_models,
            tenant_id=tenant_id
        )

        response = await llm_gateway.generate(request)

        if body.use_cache:
            await ai_cache.set_semantic(tenant_id, body.prompt, response.model_used, response.content)

        eval_report = await ai_evaluator.evaluate_response(body.prompt, response.content)

        res = GenerateResponseDTO(
            content=response.content,
            model_used=response.model_used,
            provider_used=response.provider_used,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
            cached=False,
            evaluation_score=eval_report.overall_score
        )
        return {
            "success": True,
            "message": "Text generated successfully",
            "data": res.model_dump()
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

# 2. LLM Streaming Endpoint (Server-Sent Events)
@router.post("/stream")
async def stream_text(
    body: GenerateRequestDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    try:
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=body.system_prompt),
                LLMMessage(role="user", content=body.prompt)
            ],
            primary_model=body.primary_model,
            fallback_models=body.fallback_models,
            tenant_id=tenant_id
        )

        async def sse_event_generator():
            async for chunk in llm_gateway.stream_generate(request):
                event_data = {
                    "delta": chunk.delta,
                    "model_used": chunk.model_used,
                    "provider_used": chunk.provider_used,
                    "is_final": chunk.is_final
                }
                yield f"data: {json.dumps(event_data)}\n\n"

        return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

# 3. Model Registry Endpoints
@router.get("/models", status_code=200)
async def list_models(provider: Optional[str] = None):
    models = model_registry.list_all()
    if provider:
        models = [m for m in models if m.provider.value == provider]
    data = [
        {
            "model_id": m.model_id,
            "provider": m.provider.value,
            "context_window": m.context_window,
            "supports_tools": m.supports_tools,
            "supports_vision": m.supports_vision,
            "supports_streaming": m.supports_streaming,
            "cost_per_1k_input_tokens": m.cost_per_1k_input_tokens,
            "cost_per_1k_output_tokens": m.cost_per_1k_output_tokens,
            "description": m.description
        }
        for m in models
    ]
    return {
        "success": True,
        "message": "Models listed successfully",
        "data": data
    }

# 4. Prompt Registry Endpoints
@router.post("/prompts", status_code=201)
async def register_prompt_template(dto: PromptTemplateDTO):
    try:
        tmpl = PromptTemplate(
            template_id=dto.template_id,
            version=dto.version,
            name=dto.name,
            description=dto.description,
            system_prompt=dto.system_prompt,
            user_prompt_template=dto.user_prompt_template,
            tags=dto.tags,
            variables=dto.variables
        )
        prompt_manager.register(tmpl)
        return {
            "success": True,
            "message": "Prompt template registered successfully",
            "data": {"status": "registered", "key": f"{dto.template_id}:{dto.version}"}
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

@router.get("/prompts", status_code=200)
async def list_prompt_templates(tag: Optional[str] = None):
    templates = prompt_manager.list_templates(tag=tag)
    data = [
        {
            "template_id": t.template_id,
            "version": t.version,
            "name": t.name,
            "description": t.description,
            "tags": t.tags,
            "variables": t.variables
        }
        for t in templates
    ]
    return {
        "success": True,
        "message": "Prompt templates listed successfully",
        "data": data
    }

@router.post("/prompts/render", status_code=200)
async def render_prompt(dto: RenderPromptDTO):
    try:
        rendered = prompt_manager.render(dto.template_id, dto.version, dto.variables)
        return {
            "success": True,
            "message": "Prompt rendered successfully",
            "data": rendered
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))
    except ValueError as e:
        raise NotFoundException(message=str(e))

# 5. Embedding Service Endpoint
@router.post("/embeddings", status_code=200)
async def generate_embeddings(dto: EmbeddingRequestDTO):
    if dto.texts:
        vectors = await embedding_service.embed_documents(dto.texts, provider=dto.provider)
        return {
            "success": True,
            "message": "Embeddings generated successfully",
            "data": {"vectors": vectors, "count": len(vectors), "dimension": len(vectors[0]) if vectors else 0}
        }
    elif dto.text:
        vector = await embedding_service.embed_query(dto.text, provider=dto.provider)
        return {
            "success": True,
            "message": "Embedding generated successfully",
            "data": {"vector": vector, "dimension": len(vector)}
        }
    else:
        raise BadRequestException(message="Must supply 'text' or 'texts'.")

# 6. Vector Database Endpoints
@router.post("/vector-db/upsert", status_code=200)
async def upsert_vector_records(
    dto: VectorUpsertDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    records = []
    for r in dto.records:
        r_id = r.get("id") or f"id_{len(records)}"
        text = r.get("text", "")
        vec = await embedding_service.embed_query(text)
        records.append(VectorRecord(
            id=r_id,
            vector=vec,
            payload=r.get("payload", {"text": text}),
            tenant_id=tenant_id,
            collection_name=dto.collection_name
        ))
    count = await vector_store.upsert(records, collection_name=dto.collection_name)
    return {
        "success": True,
        "message": "Vector records upserted successfully",
        "data": {"status": "success", "upserted_count": count}
    }

@router.post("/vector-db/search", status_code=200)
async def search_vector_db(
    dto: VectorSearchDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    query_vec = await embedding_service.embed_query(dto.query)
    results = await vector_store.search(
        query_vector=query_vec,
        tenant_id=tenant_id,
        collection_name=dto.collection_name,
        top_k=dto.top_k,
        filter_metadata=dto.filter_metadata
    )
    data = [
        {
            "id": r.id,
            "score": r.score,
            "payload": r.payload,
            "collection_name": r.collection_name
        }
        for r in results
    ]
    return {
        "success": True,
        "message": "Vector search completed successfully",
        "data": data
    }

# 7. Conversation Memory Endpoints
@router.post("/memory/turns", status_code=200)
async def add_conversation_turn(
    dto: AddTurnDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    try:
        domain_guardrail.enforce_policy(dto.content, context_name="Conversation Turn Content")
        mem = conversation_memory_manager.get_or_create(dto.session_id, tenant_id=tenant_id, memory_type=dto.memory_type)
        turn = mem.add_turn(dto.role, dto.content)
        return {
            "success": True,
            "message": "Conversation turn added successfully",
            "data": {"status": "added", "turn_id": turn.turn_id}
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

@router.get("/memory/{session_id}", status_code=200)
async def get_conversation_history(
    session_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    mem = conversation_memory_manager.get_or_create(session_id, tenant_id=tenant_id)
    history = mem.get_history()
    data = [
        {
            "turn_id": t.turn_id,
            "role": t.role,
            "content": t.content,
            "timestamp": t.timestamp
        }
        for t in history
    ]
    return {
        "success": True,
        "message": "Conversation history retrieved successfully",
        "data": data
    }

# 8. AI Cache Endpoints
@router.get("/cache/stats", status_code=200)
async def get_cache_stats():
    return {
        "success": True,
        "message": "Cache stats retrieved successfully",
        "data": ai_cache.get_stats()
    }

@router.post("/cache/clear", status_code=200)
async def clear_cache():
    ai_cache.clear()
    return {
        "success": True,
        "message": "Cache cleared successfully",
        "data": {"status": "cleared"}
    }

# 9. Evaluation Framework Endpoint
@router.post("/evaluate", status_code=200)
async def evaluate_response(dto: EvaluateRequestDTO):
    report = await ai_evaluator.evaluate_response(dto.prompt, dto.response, dto.context)
    data = {
        "overall_score": report.overall_score,
        "passed": report.passed,
        "summary": report.summary,
        "metrics": {
            k: {"score": v.score, "passed": v.passed, "reasoning": v.reasoning}
            for k, v in report.metrics.items()
        }
    }
    return {
        "success": True,
        "message": "Response evaluated successfully",
        "data": data
    }
