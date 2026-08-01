import { Logger } from "@ire/shared-logger";
import { ClaimAggregate } from "./domain/ClaimAggregate.js";
import { AdjudicateClaimUseCase, IClaimRepository } from "./application/AdjudicateClaimUseCase.js";

const logger = new Logger({ serviceName: "claim-lifecycle-service" });

class MockClaimRepo implements IClaimRepository {
  private store = new Map<string, ClaimAggregate>();

  public async findById(id: string, tenantId: string): Promise<ClaimAggregate | null> {
    const claim = this.store.get(id);
    if (claim && claim.tenantId === tenantId) return claim;
    return null;
  }

  public async save(claim: ClaimAggregate): Promise<void> {
    this.store.set(claim.id, claim);
  }
}

async function bootstrap() {
  logger.info("Initializing Claim Lifecycle Management Service...");
  
  const repo = new MockClaimRepo();
  const sampleClaim = ClaimAggregate.create("claim_9001", "tenant_acme_health", "EXT_REF_9001", { amount: 1250.00 });
  await repo.save(sampleClaim);

  const adjudicateUseCase = new AdjudicateClaimUseCase(repo);

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
