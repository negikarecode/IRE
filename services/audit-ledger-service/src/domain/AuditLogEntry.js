"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AuditLogAggregate = void 0;
const shared_domain_1 = require("@ire/shared-domain");
const crypto_1 = __importDefault(require("crypto"));
class AuditLogAggregate extends shared_domain_1.AggregateRoot {
    props;
    constructor(id, props) {
        super(id);
        this.props = props;
    }
    get currentHash() { return this.props.currentHash; }
    static create(id, tenantId, actorId, action, resource, resourceId, previousHash, payload) {
        const timestamp = new Date();
        const dataToHash = `${id}:${tenantId}:${actorId}:${action}:${resource}:${resourceId}:${previousHash}:${timestamp.toISOString()}:${JSON.stringify(payload)}`;
        const currentHash = crypto_1.default.createHash("sha256").update(dataToHash).digest("hex");
        return new AuditLogAggregate(id, {
            tenantId,
            actorId,
            action,
            resource,
            resourceId,
            previousHash,
            currentHash,
            timestamp,
            payload
        });
    }
}
exports.AuditLogAggregate = AuditLogAggregate;
//# sourceMappingURL=AuditLogEntry.js.map