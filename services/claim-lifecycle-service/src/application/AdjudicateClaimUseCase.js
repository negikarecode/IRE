"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AdjudicateClaimUseCase = void 0;
const shared_errors_1 = require("@ire/shared-errors");
class AdjudicateClaimUseCase {
    claimRepo;
    constructor(claimRepo) {
        this.claimRepo = claimRepo;
    }
    async execute(command) {
        const claim = await this.claimRepo.findById(command.claimId, command.tenantId);
        if (!claim) {
            throw new shared_errors_1.ValidationException(`Claim '${command.claimId}' not found for tenant '${command.tenantId}'`);
        }
        // Confidence threshold logic for AI / Rule engine decisioning
        if (command.confidenceScore < 0.85) {
            claim.escalateToHITL(`Low confidence score (${command.confidenceScore}) requires human verification.`);
        }
        else {
            claim.completeAdjudication(command.ruleResult);
        }
        await this.claimRepo.save(claim);
        return { claimId: claim.id, status: claim.status };
    }
}
exports.AdjudicateClaimUseCase = AdjudicateClaimUseCase;
//# sourceMappingURL=AdjudicateClaimUseCase.js.map