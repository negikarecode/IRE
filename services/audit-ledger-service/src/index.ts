import { Logger } from "@ire/shared-logger";
import { AuditLogAggregate } from "./domain/AuditLogEntry.js";

const logger = new Logger({ serviceName: "audit-ledger-service" });

async function bootstrap() {
  logger.info("Initializing Audit & Compliance Ledger Service...");

  const log1 = AuditLogAggregate.create(
    "audit_01",
    "tenant_acme_health",
    "system_ingestion",
    "CLAIM_INGESTED",
    "Claim",
    "claim_9001",
    "0000000000000000000000000000000000000000000000000000000000000000",
    { format: "FHIR_R4" }
  );

  logger.info("Recorded verifiable cryptographic audit log entry", {
    id: log1.id,
    hash: log1.currentHash
  });

  logger.info("Audit Ledger Service listening on port 3006.");
}

bootstrap().catch(err => {
  logger.error("Failed to start audit-ledger-service", { error: err.message });
});
