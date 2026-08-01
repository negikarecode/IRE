"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PluggableRuleRunner = void 0;
const shared_errors_1 = require("@ire/shared-errors");
class PluggableRuleRunner {
    engineType = "PLUGGABLE_AST_RUNNER";
    plugins = new Map();
    registerPlugin(plugin) {
        this.plugins.set(plugin.id, plugin);
    }
    async evaluateClaim(context) {
        const activePlugins = Array.from(this.plugins.values());
        if (activePlugins.length === 0) {
            throw new shared_errors_1.RuleExecutionException("No rule plugins registered for engine execution context.");
        }
        const traces = [];
        let isCompliant = true;
        let recommendedAction = "APPROVE";
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
exports.PluggableRuleRunner = PluggableRuleRunner;
//# sourceMappingURL=PluggableRuleRunner.js.map