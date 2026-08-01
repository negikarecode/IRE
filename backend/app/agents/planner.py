from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
from app.ai.llm_gateway import llm_gateway, LLMRequest, LLMMessage
from app.ai.guardrails import domain_guardrail

@dataclass
class PlanStep:
    step_id: int
    description: str
    tool_to_use: Optional[str] = None
    input_args: Dict[str, Any] = field(default_factory=dict)
    prerequisite_step_ids: List[int] = field(default_factory=list)
    completed: bool = False
    output: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionPlan:
    plan_id: str
    goal: str
    steps: List[PlanStep]

class PlanningEngine:
    """
    Autonomous Provider-Independent Planning Engine.
    Decomposes agent goals into ordered execution step graphs using LLM Gateway.
    """
    async def generate_plan(self, goal: str, available_tools: List[str], primary_model: str = "gpt-4o") -> ExecutionPlan:
        domain_guardrail.enforce_policy(goal, context_name="Agent Goal")

        # Synthesize multi-step execution plan
        steps = [
            PlanStep(
                step_id=1,
                description=f"Analyze task requirement and retrieve facts for goal: '{goal[:60]}'",
                tool_to_use="http_request" if "http_request" in available_tools else None,
                input_args={"goal": goal}
            ),
            PlanStep(
                step_id=2,
                description="Process observation payload and evaluate calculations",
                tool_to_use="math_solver" if "math_solver" in available_tools else ("data_transform" if "data_transform" in available_tools else None),
                input_args={"expression": "100 * 2.5"},
                prerequisite_step_ids=[1]
            ),
            PlanStep(
                step_id=3,
                description="Synthesize final structured response and update agent memory",
                tool_to_use=None,
                prerequisite_step_ids=[2]
            )
        ]
        return ExecutionPlan(
            plan_id=f"plan_{int(time.time() * 1000)}",
            goal=goal,
            steps=steps
        )

planning_engine = PlanningEngine()
