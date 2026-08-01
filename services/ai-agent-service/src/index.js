"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const shared_logger_1 = require("@ire/shared-logger");
const AgentOrchestrator_js_1 = require("./domain/AgentOrchestrator.js");
const logger = new shared_logger_1.Logger({ serviceName: "ai-agent-service" });
async function bootstrap() {
    logger.info("Initializing AI Agent Integration & Context Service...");
    const orchestrator = new AgentOrchestrator_js_1.AIAgentOrchestrator();
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
//# sourceMappingURL=index.js.map