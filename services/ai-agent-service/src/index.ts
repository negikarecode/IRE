import { Logger } from "@ire/shared-logger";
import { AIAgentOrchestrator } from "./domain/AgentOrchestrator.js";

const logger = new Logger({ serviceName: "ai-agent-service" });

async function bootstrap() {
  logger.info("Initializing AI Agent Integration & Context Service...");

  const orchestrator = new AIAgentOrchestrator();
  const agentRun = await orchestrator.runTask({
    tenantId: "tenant_acme_health",
    claimId: "claim_9001",
    conversationHistory: [
      { role: "system", content: "You are the AI Reasoning Assistant for healthcare claims." }
    ]
  });

  logger.info("AI Agent Orchestration task result", { result: agentRun });
  logger.info("AI Agent Service listening on port 3005.");
}

bootstrap().catch(err => {
  logger.error("Failed to start ai-agent-service", { error: err.message });
});
