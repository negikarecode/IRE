import { IRuleEngineProvider, IRulePlugin, RuleEvaluationContext, RuleEvaluationResult } from "@ire/shared-rule-engine-contract";
import { RuleExecutionException } from "@ire/shared-errors";

export class PluggableRuleRunner implements IRuleEngineProvider {
  public readonly engineType = "PLUGGABLE_AST_RUNNER";
  private plugins = new Map<string, IRulePlugin>();

  public registerPlugin(plugin: IRulePlugin): void {
    this.plugins.set(plugin.id, plugin);
  }

  public async evaluateClaim(context: RuleEvaluationContext): Promise<RuleEvaluationResult> {
    const activePlugins = Array.from(this.plugins.values());
    if (activePlugins.length === 0) {
      throw new RuleExecutionException("No rule plugins registered for engine execution context.");
    }

    const traces = [];
    let isCompliant = true;
    let recommendedAction: RuleEvaluationResult["recommendedAction"] = "APPROVE";

    for (const plugin of activePlugins) {
      const res = await plugin.evaluate(context);
      traces.push(...res.traces);
      if (!res.isCompliant) {
        isCompliant = false;
        recommendedAction = res.recommendedAction;
      }
    }

    return {
      evaluationId: `eval_${Date.now()}`,
      tenantId: context.tenantId,
      claimId: context.claimId,
      isCompliant,
      traces,
      recommendedAction,
      evaluatedAt: new Date()
    };
  }
}
