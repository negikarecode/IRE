from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from app.core.dependencies import get_tenant_header
from app.agents.registry import agent_registry, AgentMetadata, AgentStatus
from app.agents.lifecycle import agent_lifecycle_manager, InvalidStateTransitionException
from app.agents.execution_engine import agent_execution_engine
from app.agents.task_queue import agent_task_queue, TaskPriority
from app.agents.tool_registry import agent_tool_registry, AgentToolSpec
from app.agents.metrics import agent_metrics_collector
from app.agents.communication import agent_comm_bus, AgentMessage
from app.agents.memory import shared_agent_memory
from app.ai.guardrails import DomainPolicyViolationException

router = APIRouter()

class AgentRegisterDTO(BaseModel):
    agent_id: str
    name: str
    role_description: str
    system_prompt: str
    primary_model: str = "gpt-4o"
    allowed_tools: List[str] = []

class AgentRunDTO(BaseModel):
    agent_id: str
    goal: str
    session_id: Optional[str] = "session_01"
    timeout_seconds: Optional[float] = 60.0
    priority: int = TaskPriority.MEDIUM

class SendMessageDTO(BaseModel):
    sender_agent_id: str
    recipient_agent_id: Optional[str] = None
    message_type: str = "REQUEST"
    topic: Optional[str] = None
    content: Dict[str, Any]

class ToolRegisterDTO(BaseModel):
    name: str
    description: str
    parameters_schema: Dict[str, Any] = {}

from app.core.exceptions import BadRequestException, NotFoundException

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_agent(dto: AgentRegisterDTO):
    try:
        meta = AgentMetadata(
            agent_id=dto.agent_id,
            name=dto.name,
            role_description=dto.role_description,
            system_prompt=dto.system_prompt,
            primary_model=dto.primary_model,
            allowed_tools=dto.allowed_tools
        )
        agent_registry.register_agent(meta)
        return {
            "success": True,
            "message": "Agent registered successfully",
            "data": {"status": "REGISTERED", "agent_id": dto.agent_id}
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

@router.get("/", status_code=status.HTTP_200_OK)
async def list_agents():
    agents = agent_registry.list_agents()
    data = [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role_description": a.role_description,
            "primary_model": a.primary_model,
            "allowed_tools": a.allowed_tools,
            "status": a.status.value,
            "current_task_id": a.current_task_id
        }
        for a in agents
    ]
    return {
        "success": True,
        "message": "Agents listed successfully",
        "data": data
    }

@router.post("/run", status_code=status.HTTP_200_OK)
async def run_agent(
    body: AgentRunDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    try:
        result = await agent_execution_engine.execute_task(
            tenant_id=tenant_id,
            agent_id=body.agent_id,
            goal=body.goal,
            session_id=body.session_id,
            timeout_seconds=body.timeout_seconds
        )
        return {
            "success": True,
            "message": "Agent task executed successfully",
            "data": result
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

@router.post("/tasks/submit", status_code=status.HTTP_201_CREATED)
async def submit_task(
    body: AgentRunDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    try:
        task = agent_task_queue.submit_task(
            tenant_id=tenant_id,
            agent_id=body.agent_id,
            goal=body.goal,
            priority=body.priority,
            session_id=body.session_id
        )
        return {
            "success": True,
            "message": "Agent task submitted successfully",
            "data": {
                "task_id": task.task_id,
                "status": task.status,
                "priority": task.priority,
                "agent_id": task.agent_id,
                "created_at": task.created_at
            }
        }
    except DomainPolicyViolationException as e:
        raise BadRequestException(message=str(e))

@router.get("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def get_task_status(task_id: str):
    task = agent_task_queue.get_task(task_id)
    if not task:
        raise NotFoundException(message=f"Task '{task_id}' not found.")
    return {
        "success": True,
        "message": "Task status retrieved successfully",
        "data": {
            "task_id": task.task_id,
            "tenant_id": task.tenant_id,
            "agent_id": task.agent_id,
            "goal": task.goal,
            "status": task.status,
            "result": task.result,
            "error": task.error
        }
    }

@router.get("/tools", status_code=status.HTTP_200_OK)
async def list_tools():
    tools = agent_tool_registry.list_tools()
    data = [
        {
            "name": t.name,
            "description": t.description,
            "parameters_schema": t.parameters_schema,
            "timeout_seconds": t.timeout_seconds
        }
        for t in tools
    ]
    return {
        "success": True,
        "message": "Agent tools listed successfully",
        "data": data
    }

@router.post("/tools/register", status_code=status.HTTP_201_CREATED)
async def register_tool(dto: ToolRegisterDTO):
    spec = AgentToolSpec(
        name=dto.name,
        description=dto.description,
        parameters_schema=dto.parameters_schema,
        handler=lambda params: {"status": "executed_custom_handler", "params": params}
    )
    agent_tool_registry.register_tool(spec)
    return {
        "success": True,
        "message": "Agent tool registered successfully",
        "data": {"status": "REGISTERED", "tool_name": dto.name}
    }

@router.get("/metrics/{agent_id}", status_code=status.HTTP_200_OK)
async def get_agent_metrics(agent_id: str):
    metrics = agent_metrics_collector.get_metrics(agent_id)
    return {
        "success": True,
        "message": "Agent metrics retrieved successfully",
        "data": {
            "agent_id": metrics.agent_id,
            "total_runs": metrics.total_runs,
            "successful_runs": metrics.successful_runs,
            "failed_runs": metrics.failed_runs,
            "total_execution_time_ms": metrics.total_execution_time_ms,
            "total_tool_invocations": metrics.total_tool_invocations,
            "tool_counts": metrics.tool_counts
        }
    }

@router.post("/messages/send", status_code=status.HTTP_200_OK)
async def send_message(dto: SendMessageDTO):
    if dto.topic:
        msg = agent_comm_bus.publish(dto.topic, dto.sender_agent_id, dto.content)
        return {
            "success": True,
            "message": "Message published successfully",
            "data": {"status": "PUBLISHED", "topic": dto.topic, "message_id": msg.message_id}
        }
    else:
        msg = AgentMessage(
            message_id=f"msg_{int(time.time() * 1000)}",
            sender_agent_id=dto.sender_agent_id,
            recipient_agent_id=dto.recipient_agent_id,
            message_type=dto.message_type,
            content=dto.content
        )
        agent_comm_bus.send_message(msg)
        return {
            "success": True,
            "message": "Message sent successfully",
            "data": {"status": "SENT", "recipient": dto.recipient_agent_id, "message_id": msg.message_id}
        }

@router.get("/messages/receive/{agent_id}", status_code=status.HTTP_200_OK)
async def receive_messages(agent_id: str):
    messages = agent_comm_bus.receive_messages(agent_id)
    data = [
        {
            "message_id": m.message_id,
            "sender_agent_id": m.sender_agent_id,
            "message_type": m.message_type,
            "content": m.content,
            "timestamp": m.timestamp
        }
        for m in messages
    ]
    return {
        "success": True,
        "message": "Agent messages retrieved successfully",
        "data": data
    }

@router.get("/shared-context", status_code=status.HTTP_200_OK)
async def get_shared_context(tenant_id: str = Depends(get_tenant_header)):
    keys = shared_agent_memory.list_keys(tenant_id)
    context_data = {k: shared_agent_memory.get_context(tenant_id, k) for k in keys}
    return {
        "success": True,
        "message": "Shared agent context retrieved successfully",
        "data": {"tenant_id": tenant_id, "shared_context": context_data}
    }
