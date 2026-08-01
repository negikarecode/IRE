# Plugin Guide: Adding Business Logic Without Touching Infrastructure

This guide explains how developers, domain experts, and engineers can add custom business logic (e.g. claim rules, policy evaluations, and AI agent tools) to the **Insurance Reasoning Engine (IRE)** without modifying or redeploying core infrastructure or microservices.

---

## 1. Declarative Rule Engine Plugins

Future developers do **NOT** write code inside microservices or database layer code. They specify declarative rules using four fields:

1. **Condition**: A boolean expression evaluated safely inside an AST sandbox (e.g., `payload.total_amount > 10000 and payload.has_prior_authorization == False`).
2. **Severity**: `CRITICAL`, `WARNING`, or `INFO`.
3. **Explanation**: A human-readable templated explanation (e.g., `"Claim amount ${payload.total_amount} exceeds limit without authorization."`).
4. **Suggestion**: Recommended action (e.g., `"Route claim for manual authorization."`).

### How to Register a Rule via REST API

```bash
curl -X POST "http://localhost:8000/api/v1/rules/register" \
     -H "Content-Type: application/json" \
     -d '{
       "rule_id": "RULE_EXCEED_LIMIT_01",
       "name": "High Amount Prior Auth Verification",
       "version": "1.0.0",
       "condition": "payload.total_amount > 10000 and payload.has_prior_authorization == False",
       "severity": "CRITICAL",
       "explanation": "Claim amount ${payload.total_amount} exceeds prior auth limit.",
       "suggestion": "Escalate claim to senior auditor for manual review.",
       "priority": 150,
       "dependencies": []
     }'
```

### Automatic Rule Execution Flow

When a claim payload is submitted to `POST /api/v1/rules/execute`, the engine automatically:
1. Sorts active rules by priority.
2. Resolves prerequisite rule dependencies.
3. Evaluates condition in an isolated AST sandbox (`SafeRuleSandbox`).
4. Interpolates variable templates into explanations/suggestions.
5. Returns a structured `RuleExecutionReport`.

---

## 2. Autonomous AI Agent Tool Plugins

Developers can equip autonomous agents with custom tools by registering them with `agent_tool_registry`.

### Creating a Custom Tool Plugin (Python Example)

```python
from app.agents.tool_registry import agent_tool_registry, AgentToolSpec

def my_custom_verification_tool(args: dict) -> dict:
    query = args.get("query")
    # Custom business/data lookup logic here
    return {"status": "VERIFIED", "result_data": f"Processed {query}"}

# Register the tool
agent_tool_registry.register_tool(
    AgentToolSpec(
        name="custom_verifier_tool",
        description="Verifies external parameters against custom databases.",
        parameters_schema={"query": {"type": "string"}},
        handler=my_custom_verification_tool,
        timeout_seconds=15.0
    )
)
```

Once registered, agents assigned `allowed_tools: ["custom_verifier_tool"]` will automatically invoke the tool during ReAct planning execution!

---

## 3. WebAssembly (WASM) & DSL Rule Plugins

For ultra-low latency or compiled DSL rules, developers implement the `@ire/shared-rule-engine-contract` TypeScript interface:

```typescript
import { IRulePlugin, RuleEvaluationContext, RuleEvaluationResult } from "@ire/shared-rule-engine-contract";

export class CustomDomainPlugin implements IRulePlugin {
  public id = "plugin_custom_dsl";
  public name = "Custom WASM Rule Plugin";
  public version = "1.0.0";

  public async evaluate(context: RuleEvaluationContext): Promise<RuleEvaluationResult> {
    // Custom evaluation logic here
    return {
      evaluationId: `eval_${Date.now()}`,
      tenantId: context.tenantId,
      claimId: context.claimId,
      isCompliant: true,
      traces: [],
      recommendedAction: "APPROVE",
      evaluatedAt: new Date()
    };
  }
}
```

By decoupling rule definitions into declarative JSON schemas, WASM modules, and Tool Specifications, domain logic can evolve continuously without risking core infrastructure stability.
