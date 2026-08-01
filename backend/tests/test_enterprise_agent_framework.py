import pytest
import asyncio

from app.agents.registry import agent_registry, AgentMetadata, AgentStatus
from app.agents.lifecycle import agent_lifecycle_manager, InvalidStateTransitionException
from app.agents.tool_registry import agent_tool_registry, BaseAgentTool, AgentToolSpec
from app.agents.planner import planning_engine
from app.agents.task_queue import agent_task_queue, TaskPriority
from app.agents.communication import agent_comm_bus, AgentMessage
from app.agents.memory import shared_agent_memory
from app.agents.execution_engine import agent_execution_engine
from app.agents.metrics import agent_metrics_collector
from app.agents.observation_store import observation_store
from app.ai.guardrails import DomainPolicyViolationException

def run_async(coro):
    return asyncio.run(coro)

# 1. Test Domain Guardrails in Agent Registry
def test_agent_registry_domain_guardrail():
    # Attempt registering medical agent
    with pytest.raises(DomainPolicyViolationException):
        agent_registry.register_agent(AgentMetadata(
            agent_id="bad_medical_agent",
            name="Medical Doctor Agent",
            role_description="Diagnose patient symptoms and issue prescriptions",
            system_prompt="You are a medical doctor providing clinical diagnosis."
        ))

    # Attempt registering insurance agent
    with pytest.raises(DomainPolicyViolationException):
        agent_registry.register_agent(AgentMetadata(
            agent_id="bad_insurance_agent",
            name="Insurance Claims Agent",
            role_description="Process insurance claims and check policy coverage",
            system_prompt="You are an insurance underwriter processing claims."
        ))

# 2. Test Agent Registry & Lifecycle State Machine
def test_agent_lifecycle_state_machine():
    agent_id = "test_lifecycle_agent"
    meta = AgentMetadata(
        agent_id=agent_id,
        name="Lifecycle Test Agent",
        role_description="Agent for state machine validation",
        system_prompt="You are a state machine test assistant.",
        primary_model="gpt-4o"
    )
    agent_registry.register_agent(meta)

    # INITIALIZED -> PLANNING -> RUNNING -> COMPLETED
    assert agent_lifecycle_manager.transition(agent_id, AgentStatus.PLANNING) == AgentStatus.PLANNING
    assert agent_lifecycle_manager.transition(agent_id, AgentStatus.RUNNING) == AgentStatus.RUNNING
    assert agent_lifecycle_manager.transition(agent_id, AgentStatus.COMPLETED) == AgentStatus.COMPLETED

    # Reset to IDLE for next run
    assert agent_lifecycle_manager.transition(agent_id, AgentStatus.IDLE) == AgentStatus.IDLE

    # Invalid transition (COMPLETED directly to WAITING_FOR_INPUT) should raise exception
    agent_registry.update_status(agent_id, AgentStatus.COMPLETED)
    with pytest.raises(InvalidStateTransitionException):
        agent_lifecycle_manager.transition(agent_id, AgentStatus.WAITING_FOR_INPUT)

# 3. Test Tool Registry & Custom Plugin Tool Extension
def test_tool_registry_extension():
    class CustomStringUpperTool(BaseAgentTool):
        @property
        def name(self) -> str:
            return "string_upper"

        @property
        def description(self) -> str:
            return "Converts input text to uppercase"

        def run(self, params: dict) -> dict:
            txt = str(params.get("text", ""))
            return {"uppercase": txt.upper()}

    # Register custom tool without editing framework code
    agent_tool_registry.register_class_tool(CustomStringUpperTool())
    
    spec = agent_tool_registry.get_tool("string_upper")
    assert spec is not None
    res = spec.handler({"text": "hello framework"})
    assert res["uppercase"] == "HELLO FRAMEWORK"

# 4. Test Autonomous Planner
def test_autonomous_planner():
    async def _test():
        plan = await planning_engine.generate_plan(
            goal="Analyze linear regression algorithms and plot optimization chart.",
            available_tools=["http_request", "math_solver"]
        )
        assert len(plan.steps) == 3
        assert plan.steps[0].step_id == 1
        assert plan.steps[1].prerequisite_step_ids == [1]

    run_async(_test())

# 5. Test Priority Task Queue
def test_priority_task_queue():
    q = agent_task_queue
    t_low = q.submit_task("tenant_1", "agent_a", "Low priority goal", priority=TaskPriority.LOW)
    t_high = q.submit_task("tenant_1", "agent_b", "High priority goal", priority=TaskPriority.HIGH)
    t_med = q.submit_task("tenant_1", "agent_c", "Medium priority goal", priority=TaskPriority.MEDIUM)

    # Next task popped must be HIGH priority (t_high)
    next_t1 = q.pop_next_task()
    assert next_t1.task_id == t_high.task_id

    # Next task popped must be MEDIUM priority (t_med)
    next_t2 = q.pop_next_task()
    assert next_t2.task_id == t_med.task_id

# 6. Test Communication Bus (Direct P2P & Pub/Sub Topic)
def test_communication_bus():
    # Direct P2P Messaging
    msg = AgentMessage(
        message_id="msg_001",
        sender_agent_id="agent_sender",
        recipient_agent_id="agent_receiver",
        message_type="REQUEST",
        content={"query": "Perform data lookup"}
    )
    agent_comm_bus.send_message(msg)

    received = agent_comm_bus.receive_messages("agent_receiver")
    assert len(received) == 1
    assert received[0].content["query"] == "Perform data lookup"

    # Pub/Sub Topic Channels
    received_pubsub = []
    agent_comm_bus.subscribe("data_events", lambda m: received_pubsub.append(m))

    agent_comm_bus.publish("data_events", "agent_publisher", {"event": "dataset_ready"})
    assert len(received_pubsub) == 1
    assert received_pubsub[0].content["event"] == "dataset_ready"

# 7. Test Shared Context Memory
def test_shared_context_memory():
    shared_agent_memory.set_context("tenant_org_1", "config_threshold", 99.5)
    val = shared_agent_memory.get_context("tenant_org_1", "config_threshold")
    assert val == 99.5

# 8. Test Execution Engine Runtime Execution
def test_agent_execution_engine():
    async def _test():
        agent_id = "general_assistant_agent"
        result = await agent_execution_engine.execute_task(
            tenant_id="tenant_exec_test",
            agent_id=agent_id,
            goal="Synthesize microservices circuit breaker resilience patterns."
        )

        assert result["status"] == "COMPLETED"
        assert "duration_ms" in result
        assert len(result["step_traces"]) >= 3
        assert result["confidence_score"] > 0.0

        # Verify observation store recorded environment steps
        obs_list = observation_store.get_by_agent(agent_id)
        assert len(obs_list) > 0

        # Verify metrics collector recorded run telemetry
        metrics = agent_metrics_collector.get_metrics(agent_id)
        assert metrics.total_runs >= 1
        assert metrics.successful_runs >= 1

    run_async(_test())
