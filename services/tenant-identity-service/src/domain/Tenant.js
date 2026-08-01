"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TenantAggregate = void 0;
const shared_domain_1 = require("@ire/shared-domain");
class TenantAggregate extends shared_domain_1.AggregateRoot {
    props;
    constructor(id, props) {
        super(id);
        this.props = props;
    }
    get name() { return this.props.name; }
    get slug() { return this.props.slug; }
    get isolationStrategy() { return this.props.isolationStrategy; }
    get status() { return this.props.status; }
    static create(id, name, slug, isolationStrategy) {
        const tenant = new TenantAggregate(id, {
            name,
            slug,
            isolationStrategy,
            status: "PROVISIONING",
            createdAt: new Date()
        });
        tenant.addDomainEvent({
            eventId: `evt_${Date.now()}`,
            occurredOn: new Date(),
            tenantId: id,
            aggregateId: id,
            eventType: "TenantCreatedEvent",
            payload: { name, slug, isolationStrategy }
        });
        return tenant;
    }
    activate() {
        this.props.status = "ACTIVE";
    }
}
exports.TenantAggregate = TenantAggregate;
//# sourceMappingURL=Tenant.js.map