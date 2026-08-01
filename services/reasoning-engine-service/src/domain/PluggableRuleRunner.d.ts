import { IRuleEngineProvider, IRulePlugin, RuleEvaluationContext, RuleEvaluationResult } from "@ire/shared-rule-engine-contract";
export declare class PluggableRuleRunner implements IRuleEngineProvider {
    readonly engineType = "PLUGGABLE_AST_RUNNER";
    private plugins;
    registerPlugin(plugin: IRulePlugin): void;
    evaluateClaim(context: RuleEvaluationContext): Promise<RuleEvaluationResult>;
}
