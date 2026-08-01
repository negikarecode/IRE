import { AggregateRoot } from "@ire/shared-domain";
export type ClaimStatus = "INGESTED" | "IN_REASONING" | "ADJUDICATED" | "ESCALATED_HITL" | "REJECTED" | "PAID";
export interface ClaimProps {
    tenantId: string;
    externalClaimReference: string;
    status: ClaimStatus;
    payload: Record<string, unknown>;
    adjudicationResult?: Record<string, unknown>;
    createdAt: Date;
    updatedAt: Date;
}
export declare class ClaimAggregate extends AggregateRoot<string> {
    private props;
    constructor(id: string, props: ClaimProps);
    get tenantId(): string;
    get status(): ClaimStatus;
    get payload(): Record<string, unknown>;
    get adjudicationResult(): Record<string, unknown> | undefined;
    static create(id: string, tenantId: string, externalClaimReference: string, payload: Record<string, unknown>): ClaimAggregate;
    transitionToReasoning(): void;
    completeAdjudication(result: Record<string, unknown>): void;
    escalateToHITL(reason: string): void;
}
