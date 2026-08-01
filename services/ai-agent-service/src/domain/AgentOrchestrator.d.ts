import { AgentPromptContext, AgentReasoningStep, IAgentOrchestrator, IAgentTool } from "@ire/shared-ai-agent-contract";
export declare class AIAgentOrchestrator implements IAgentOrchestrator {
    private registeredTools;
    registerTool(tool: IAgentTool): void;
    runTask(promptContext: AgentPromptContext): Promise<{
        summary: string;
        reasoningSteps: AgentReasoningStep[];
        hitlTaskRequired?: any;
    }>;
}
