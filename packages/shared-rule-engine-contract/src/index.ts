/**
 * Rule Engine Plugin System Contract
 * Zero hardcoded domain rules. Domain experts provide rules via configuration, WASM modules, or DSL.
 */

export interface RuleEvaluationContext {
  tenantId: string;
  claimId: string;
  claimPayload: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface RuleExecutionNodeTrace {
  ruleId: string;
  ruleName: string;
  evaluatedAt: Date;
  status: "PASSED" | "FAILED" | "SKIPPED" | "ERROR";
  reason?: string;
  executionTimeMs: number;
  outputFlags?: Record<string, unknown>;
}

export interface RuleEvaluationResult {
  evaluationId: string;
  tenantId: string;
  claimId: string;
  isCompliant: boolean;
  score?: number;
  traces: RuleExecutionNodeTrace[];
  recommendedAction: "APPROVE" | "DENY" | "MANUAL_REVIEW" | "REQUEST_INFO";
  evaluatedAt: Date;
}

export interface IRulePlugin {
  id: string;
  name: string;
  version: string;
  evaluate(context: RuleEvaluationContext): Promise<RuleEvaluationResult>;
}

export interface IRuleEngineProvider {
  engineType: string;
  registerPlugin(plugin: IRulePlugin): void;
  evaluateClaim(context: RuleEvaluationContext): Promise<RuleEvaluationResult>;
}
