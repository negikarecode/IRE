"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const shared_logger_1 = require("@ire/shared-logger");
const AuditLogEntry_js_1 = require("./domain/AuditLogEntry.js");
const logger = new shared_logger_1.Logger({ serviceName: "audit-ledger-service" });
async function bootstrap() {
    logger.info("Initializing Audit & Compliance Ledger Service...");
    const log1 = AuditLogEntry_js_1.AuditLogAggregate.create("audit_01", "tenant_acme_health", "system_ingestion", "CLAIM_INGESTED", "Claim", "claim_9001", "0000000000000000000000000000000000000000000000000000000000000000", { format: "FHIR_R4" });
    logger.info("Recorded verifiable cryptographic audit log entry", {
        id: log1.id,
        hash: log1.currentHash
    });
    logger.info("Audit Ledger Service listening on port 3006.");
}
bootstrap().catch(err => {
    logger.error("Failed to start audit-ledger-service", { error: err.message });
});
//# sourceMappingURL=index.js.map