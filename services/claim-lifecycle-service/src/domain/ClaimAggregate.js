"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClaimAggregate = void 0;
const shared_domain_1 = require("@ire/shared-domain");
class ClaimAggregate extends shared_domain_1.AggregateRoot {
    props;
    constructor(id, props) {
        super(id);
        this.props = props;
    }
    get tenantId() { return this.props.tenantId; }
    get status() { return this.props.status; }
    get payload() { return this.props.payload; }
    get adjudicationResult() { return this.props.adjudicationResult; }
    static create(id, tenantId, externalClaimReference, payload) {
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
    transitionToReasoning() {
        this.props.status = "IN_REASONING";
        this.props.updatedAt = new Date();
    }
    completeAdjudication(result) {
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
    escalateToHITL(reason) {
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
exports.ClaimAggregate = ClaimAggregate;
//# sourceMappingURL=ClaimAggregate.js.map