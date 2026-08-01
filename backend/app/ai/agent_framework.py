from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional
import time
from app.ai.llm_gateway import llm_gateway, LLMRequest, LLMMessage
from app.ai.conversation_memory import conversation_memory_manager
from app.ai.caching import ai_cache
from app.ai.retry_pipeline import retry_pipeline
from app.ai.guardrails import domain_guardrail
from app.ai.evaluator import ai_evaluator

@dataclass
class AgentTool:
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    func: Callable[[Dict[str, Any]], Any]

@dataclass
class AgentStepTrace:
    step_number: int
    thought: str
    action: Optional[str]
    action_input: Optional[Dict[str, Any]]
    action_output: Optional[Dict[str, Any]]
    timestamp: float

@dataclass
class AgentExecutionResult:
    agent_id: str
    final_answer: str
    steps: List[AgentStepTrace]
    confidence_score: float
    requires_hitl: bool

class AIAgentFramework:
    """
    Autonomous ReAct / Tool-calling Agent Orchestration Framework.
    Leverages provider-independent AI infrastructure, conversation memory, caching,
    retry pipeline, evaluation framework, and domain policy guardrails.
    """
    def __init__(self, agent_id: str, primary_model: str = "gpt-4o"):
        self.agent_id = agent_id
        self.primary_model = primary_model
        self._tools: Dict[str, AgentTool] = {}

    def register_tool(self, tool: AgentTool):
        self._tools[tool.name] = tool

    async def run(
        self,
        tenant_id: str,
        prompt: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentExecutionResult:
        # Enforce domain policy guardrail (rejects medical & insurance prompts)
        domain_guardrail.enforce_policy(prompt, context_name=f"Agent '{self.agent_id}' Prompt")

        steps: List[AgentStepTrace] = []
        sess_id = session_id or f"sess_{int(time.time())}"
        memory = conversation_memory_manager.get_or_create(sess_id, tenant_id=tenant_id)
        
        # Add user prompt turn to memory
        memory.add_turn(role="user", content=prompt)

        # Step 1: Reasoning Step
        steps.append(AgentStepTrace(
            step_number=1,
            thought=f"Analyzed query. Utilizing primary model '{self.primary_model}' across provider-independent gateway.",
            action=None,
            action_input=None,
            action_output=None,
            timestamp=time.time()
        ))

        # Check Cache
        cached_resp = await ai_cache.get_semantic(tenant_id, prompt, self.primary_model)
        if cached_resp:
            memory.add_turn(role="assistant", content=cached_resp)
            return AgentExecutionResult(
                agent_id=self.agent_id,
                final_answer=cached_resp,
                steps=steps,
                confidence_score=0.98,
                requires_hitl=False
            )

        # Step 2: LLM Gateway execution via retry pipeline
        request = LLMRequest(
            messages=[LLMMessage(role=turn.role, content=turn.content) for turn in memory.get_history()],
            primary_model=self.primary_model,
            tenant_id=tenant_id
        )

        response = await retry_pipeline.execute(llm_gateway.generate, request)

        # Step 3: Tool Call Execution (if registered)
        if self._tools:
            tool_name = list(self._tools.keys())[0]
            tool = self._tools[tool_name]
            tool_res = tool.func({"query": prompt})

            steps.append(AgentStepTrace(
                step_number=2,
                thought=f"Invoked tool '{tool_name}'.",
                action=tool_name,
                action_input={"query": prompt},
                action_output=tool_res if isinstance(tool_res, dict) else {"output": str(tool_res)},
                timestamp=time.time()
            ))

        final_answer = response.content
        # Cache response
        await ai_cache.set_semantic(tenant_id, prompt, self.primary_model, final_answer)
        # Store assistant response turn
        memory.add_turn(role="assistant", content=final_answer)

        # Step 4: Quality Evaluation
        eval_report = await ai_evaluator.evaluate_response(prompt, final_answer)

        return AgentExecutionResult(
            agent_id=self.agent_id,
            final_answer=final_answer,
            steps=steps,
            confidence_score=eval_report.overall_score,
            requires_hitl=not eval_report.passed
        )
