import { Logger } from "@ire/shared-logger";
import { PluggableRuleRunner } from "./domain/PluggableRuleRunner.js";
import { IRulePlugin, RuleEvaluationContext, RuleEvaluationResult } from "@ire/shared-rule-engine-contract";

const logger = new Logger({ serviceName: "reasoning-engine-service" });

/**
 * Generic Structural Data Validation Rule Plugin Example
 * Demonstrates pluggability without incorporating domain-specific medical/insurance logic.
 */
class StructuralValidationPlugin implements IRulePlugin {
  public id = "plugin_structural_validator";
  public name = "Structural Data Completeness Plugin";
  public version = "1.0.0";

  public async evaluate(context: RuleEvaluationContext): Promise<RuleEvaluationResult> {
    const hasClaimId = Boolean(context.claimId);
    const hasPayload = Boolean(context.claimPayload);
    const isValid = hasClaimId && hasPayload;

    return {
      evaluationId: `eval_struct_${Date.now()}`,
      tenantId: context.tenantId,
      claimId: context.claimId,
      isCompliant: isValid,
      traces: [{
        ruleId: "RULE_STRUCT_01",
        ruleName: "Check Claim Field Presence",
        evaluatedAt: new Date(),
        status: isValid ? "PASSED" : "FAILED",
        executionTimeMs: 1.2
      }],
      recommendedAction: isValid ? "APPROVE" : "MANUAL_REVIEW",
      evaluatedAt: new Date()
    };
  }
}

async function bootstrap() {
  logger.info("Initializing Reasoning Engine Service...");
  
  const runner = new PluggableRuleRunner();
  runner.registerPlugin(new StructuralValidationPlugin());

  const evalResult = await runner.evaluateClaim({
    tenantId: "tenant_acme_health",
    claimId: "claim_9001",
    claimPayload: { providerId: "P123" },
    metadata: { source: "test" }
  });

  logger.info("Executed Pluggable Rule Evaluation Engine", { result: evalResult });
  logger.info("Reasoning Engine Service listening on port 3004.");
}

bootstrap().catch(err => {
  logger.error("Failed to start reasoning-engine-service", { error: err.message });
});
