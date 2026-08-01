import { ClaimAggregate } from "../domain/ClaimAggregate.js";
import { ValidationException } from "@ire/shared-errors";

export interface AdjudicateClaimCommand {
  claimId: string;
  tenantId: string;
  ruleResult: Record<string, unknown>;
  confidenceScore: number;
}

export interface IClaimRepository {
  findById(id: string, tenantId: string): Promise<ClaimAggregate | null>;
  save(claim: ClaimAggregate): Promise<void>;
}

export class AdjudicateClaimUseCase {
  constructor(private claimRepo: IClaimRepository) {}

  public async execute(command: AdjudicateClaimCommand): Promise<{ claimId: string; status: string }> {
    const claim = await this.claimRepo.findById(command.claimId, command.tenantId);
    if (!claim) {
      throw new ValidationException(`Claim '${command.claimId}' not found for tenant '${command.tenantId}'`);
    }

    // Confidence threshold logic for AI / Rule engine decisioning
    if (command.confidenceScore < 0.85) {
      claim.escalateToHITL(`Low confidence score (${command.confidenceScore}) requires human verification.`);
    } else {
      claim.completeAdjudication(command.ruleResult);
    }

    await this.claimRepo.save(claim);
    return { claimId: claim.id, status: claim.status };
  }
}
