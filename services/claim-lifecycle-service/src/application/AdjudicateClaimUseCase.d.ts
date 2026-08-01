import { ClaimAggregate } from "../domain/ClaimAggregate.js";
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
export declare class AdjudicateClaimUseCase {
    private claimRepo;
    constructor(claimRepo: IClaimRepository);
    execute(command: AdjudicateClaimCommand): Promise<{
        claimId: string;
        status: string;
    }>;
}
