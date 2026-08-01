import { AggregateRoot, ClaimId } from "@ire/shared-domain";

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

export class ClaimAggregate extends AggregateRoot<string> {
  private props: ClaimProps;

  constructor(id: string, props: ClaimProps) {
    super(id);
    this.props = props;
  }

  get tenantId(): string { return this.props.tenantId; }
  get status(): ClaimStatus { return this.props.status; }
  get payload(): Record<string, unknown> { return this.props.payload; }
  get adjudicationResult(): Record<string, unknown> | undefined { return this.props.adjudicationResult; }

  public static create(id: string, tenantId: string, externalClaimReference: string, payload: Record<string, unknown>): ClaimAggregate {
    const claim = new ClaimAggregate(id, {
      tenantId,
      externalClaimReference,
      status: "INGESTED",
      payload,
      createdAt: new Date(),
      updatedAt: new Date()
    });

    claim.addDomainEvent({
      eventId: `evt_claim_created_${Date.now()}`,
      occurredOn: new Date(),
      tenantId,
      aggregateId: id,
      eventType: "ClaimCreatedEvent",
      payload: { claimId: id, externalClaimReference }
    });

    return claim;
  }

  public transitionToReasoning(): void {
    this.props.status = "IN_REASONING";
    this.props.updatedAt = new Date();
  }

  public completeAdjudication(result: Record<string, unknown>): void {
    this.props.status = "ADJUDICATED";
    this.props.adjudicationResult = result;
    this.props.updatedAt = new Date();

    this.addDomainEvent({
      eventId: `evt_claim_adjudicated_${Date.now()}`,
      occurredOn: new Date(),
      tenantId: this.props.tenantId,
      aggregateId: this.id,
      eventType: "ClaimAdjudicatedEvent",
      payload: { claimId: this.id, adjudicationResult: result }
    });
  }

  public escalateToHITL(reason: string): void {
    this.props.status = "ESCALATED_HITL";
    this.props.updatedAt = new Date();

    this.addDomainEvent({
      eventId: `evt_claim_hitl_${Date.now()}`,
      occurredOn: new Date(),
      tenantId: this.props.tenantId,
      aggregateId: this.id,
      eventType: "ClaimEscalatedToHITLEvent",
      payload: { claimId: this.id, reason }
    });
  }
}
