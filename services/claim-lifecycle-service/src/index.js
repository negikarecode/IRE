"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const shared_logger_1 = require("@ire/shared-logger");
const ClaimAggregate_js_1 = require("./domain/ClaimAggregate.js");
const AdjudicateClaimUseCase_js_1 = require("./application/AdjudicateClaimUseCase.js");
const logger = new shared_logger_1.Logger({ serviceName: "claim-lifecycle-service" });
class MockClaimRepo {
    store = new Map();
    async findById(id, tenantId) {
        const claim = this.store.get(id);
        if (claim && claim.tenantId === tenantId)
            return claim;
        return null;
    }
    async save(claim) {
        this.store.set(claim.id, claim);
    }
}
async function bootstrap() {
    logger.info("Initializing Claim Lifecycle Management Service...");
    const repo = new MockClaimRepo();
    const sampleClaim = ClaimAggregate_js_1.ClaimAggregate.create("claim_9001", "tenant_acme_health", "EXT_REF_9001", { amount: 1250.00 });
    await repo.save(sampleClaim);
    const adjudicateUseCase = new AdjudicateClaimUseCase_js_1.AdjudicateClaimUseCase(repo);
    const highConfResult = await adjudicateUseCase.execute({
        claimId: "claim_9001",
        tenantId: "tenant_acme_health",
        ruleResult: { recommendation: "APPROVE", code: "AUTO_PASS" },
        confidenceScore: 0.98
    });
    logger.info("Claim Adjudication execution result", { result: highConfResult });
    logger.info("Claim Lifecycle Service listening on port 3003.");
}
bootstrap().catch(err => {
    logger.error("Failed to start claim-lifecycle-service", { error: err.message });
});
//# sourceMappingURL=index.js.map