"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IngestedPayloadAggregate = void 0;
const shared_domain_1 = require("@ire/shared-domain");
class IngestedPayloadAggregate extends shared_domain_1.AggregateRoot {
    props;
    constructor(id, props) {
        super(id);
        this.props = props;
    }
    get tenantId() { return this.props.tenantId; }
    get format() { return this.props.format; }
    get rawContent() { return this.props.rawContent; }
    static create(id, tenantId, sourceSystem, format, rawContent) {
        const aggregate = new IngestedPayloadAggregate(id, {
            tenantId,
            sourceSystem,
            format,
            rawContent,
            ingestedAt: new Date()
        });
        aggregate.addDomainEvent({
            eventId: `evt_ingest_${Date.now()}`,
            occurredOn: new Date(),
            tenantId,
            aggregateId: id,
            eventType: "ClaimPayloadIngestedEvent",
            payload: { payloadId: id, format, sourceSystem }
        });
        return aggregate;
    }
}
exports.IngestedPayloadAggregate = IngestedPayloadAggregate;
//# sourceMappingURL=IngestedPayload.js.map