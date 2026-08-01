import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from app.agents.registry import agent_registry, AgentStatus
from app.agents.lifecycle import agent_lifecycle_manager
from app.agents.tool_registry import agent_tool_registry
from app.agents.memory import shared_agent_memory
from app.ai.conversation_memory import conversation_memory_manager
from app.agents.observation_store import observation_store
from app.agents.planner import planning_engine
from app.agents.metrics import agent_metrics_collector
from app.ai.retry_pipeline import retry_pipeline
from app.ai.evaluator import ai_evaluator
from app.ai.guardrails import domain_guardrail, DomainPolicyViolationException

logger = logging.getLogger("agent_execution_engine")

class AgentExecutionEngine:
    """
    Production Enterprise AI Agent Execution Engine.
    Coordinates: Lifecycle -> Planning -> Tool Execution (with Retry & Timeout) ->
    Observation Store -> Shared Memory -> Quality Evaluation -> Telemetry Metrics.
    """
    async def execute_task(
        self,
        tenant_id: str,
        agent_id: str,
        goal: str,
        session_id: str = "default_session",
        timeout_seconds: float = 60.0,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        # Enforce domain policy guardrail (rejection of medical & insurance prompts)
        domain_guardrail.enforce_policy(goal, context_name=f"Agent '{agent_id}' Goal")

        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found in registry.")

        # Lifecycle transition: PLANNING
        agent_lifecycle_manager.transition(agent_id, AgentStatus.PLANNING)
        start_time = time.time()

        memory = conversation_memory_manager.get_or_create(session_id, tenant_id=tenant_id, memory_type="sliding")
        memory.add_turn("system", agent.system_prompt)
        memory.add_turn("user", goal)

        tool_calls_executed = []
        step_traces = []

        try:
            async def _run_loop():
                # 1. Generate Execution Plan
                plan = await planning_engine.generate_plan(goal, agent.allowed_tools, primary_model=agent.primary_model)

                # Lifecycle transition: RUNNING
                agent_lifecycle_manager.transition(agent_id, AgentStatus.RUNNING)

                for step in plan.steps:
                    step_start = time.time()
                    tool_output = None

                    # Tool execution with retry pipeline & timeout handling
                    if step.tool_to_use and step.tool_to_use in agent.allowed_tools:
                        tool_spec = agent_tool_registry.get_tool(step.tool_to_use)
                        if tool_spec:
                            async def _tool_caller():
                                return await asyncio.wait_for(
                                    asyncio.to_thread(tool_spec.handler, step.input_args),
                                    timeout=tool_spec.timeout_seconds
                                )

                            try:
                                tool_output = await retry_pipeline.execute(_tool_caller)
                                tool_calls_executed.append(step.tool_to_use)
                            except Exception as err:
                                logger.warning(f"Tool '{step.tool_to_use}' failed execution: {str(err)}")
                                tool_output = {"error": str(err)}

                    # 2. Record Observation in Observation Store
                    obs_id = observation_store.record(
                        agent_id=agent_id,
                        step_number=step.step_id,
                        source_tool=step.tool_to_use or "internal_planner",
                        raw_payload=tool_output or {"description": step.description}
                    )

                    step_traces.append({
                        "step_id": step.step_id,
                        "description": step.description,
                        "tool_used": step.tool_to_use,
                        "observation_id": obs_id,
                        "output": tool_output,
                        "step_time_ms": round((time.time() - step_start) * 1000, 2)
                    })

                summary = f"Goal '{goal[:50]}...' executed successfully by agent '{agent_id}' across {len(plan.steps)} steps."
                memory.add_turn("assistant", summary)
                return summary

            result_summary = await asyncio.wait_for(_run_loop(), timeout=timeout_seconds)
            duration_ms = (time.time() - start_time) * 1000

            # Evaluate execution output quality
            eval_report = await ai_evaluator.evaluate_response(goal, result_summary)

            # Lifecycle transition: COMPLETED
            agent_lifecycle_manager.transition(agent_id, AgentStatus.COMPLETED)
            agent_metrics_collector.record_run(agent_id, True, duration_ms, tool_calls_executed)

            # Record in shared context
            shared_agent_memory.set_context(tenant_id, f"agent_last_result_{agent_id}", {
                "summary": result_summary,
                "confidence_score": eval_report.overall_score
            })

            return {
                "agent_id": agent_id,
                "status": "COMPLETED",
                "goal": goal,
                "summary": result_summary,
                "confidence_score": eval_report.overall_score,
                "duration_ms": round(duration_ms, 2),
                "step_traces": step_traces
            }

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            agent_lifecycle_manager.transition(agent_id, AgentStatus.FAILED)
            agent_metrics_collector.record_run(agent_id, False, duration_ms, tool_calls_executed)
            return {
                "agent_id": agent_id,
                "status": "TIMED_OUT",
                "error": f"Agent execution exceeded global timeout of {timeout_seconds}s."
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            agent_lifecycle_manager.transition(agent_id, AgentStatus.FAILED)
            agent_metrics_collector.record_run(agent_id, False, duration_ms, tool_calls_executed)
            return {
                "agent_id": agent_id,
                "status": "FAILED",
                "error": str(e)
            }

agent_execution_engine = AgentExecutionEngine()
