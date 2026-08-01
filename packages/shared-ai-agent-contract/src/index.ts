/**
 * AI Agent Orchestration & Tool Contracts
 * Provides pluggable hooks for autonomous LLM reasoning agents, Memory retrieval, and Human-In-The-Loop.
 */

export interface AgentToolDeclaration {
  name: string;
  description: string;
  parametersSchema: Record<string, unknown>;
}

export interface AgentToolExecutionContext {
  tenantId: string;
  agentId: string;
  sessionId: string;
}

export interface IAgentTool {
  declaration: AgentToolDeclaration;
  execute(args: Record<string, unknown>, context: AgentToolExecutionContext): Promise<Record<string, unknown>>;
}

export interface AgentPromptContext {
  tenantId: string;
  claimId: string;
  ruleEvaluationResults?: Record<string, unknown>;
  patientContextMasked?: Record<string, unknown>;
  conversationHistory: Array<{ role: "system" | "user" | "assistant" | "tool"; content: string }>;
}

export interface AgentReasoningStep {
  stepId: string;
  thought: string;
  actionRequested?: string;
  actionArgs?: Record<string, unknown>;
  actionResult?: Record<string, unknown>;
  timestamp: Date;
}

export interface HumanInTheLoopTask {
  taskId: string;
  tenantId: string;
  claimId: string;
  agentId: string;
  reasonForEscalation: string;
  proposedResolution: Record<string, unknown>;
  status: "PENDING_HUMAN_REVIEW" | "APPROVED" | "REJECTED" | "OVERRIDDEN";
  createdAt: Date;
}

export interface IAgentOrchestrator {
  runTask(promptContext: AgentPromptContext): Promise<{
    summary: string;
    reasoningSteps: AgentReasoningStep[];
    hitlTaskRequired?: HumanInTheLoopTask;
  }>;
}
