"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const shared_logger_1 = require("@ire/shared-logger");
const IngestClaimUseCase_js_1 = require("./application/IngestClaimUseCase.js");
const logger = new shared_logger_1.Logger({ serviceName: "ingestion-service" });
class MockEventPublisher {
    async publish(event) {
        logger.info("Published CloudEvent to Kafka/RabbitMQ", { eventId: event.id, type: event.type, tenant: event.tenantid });
    }
    async publishBatch(events) {
        for (const e of events)
            await this.publish(e);
    }
}
async function bootstrap() {
    logger.info("Initializing Ingestion & EHR Integration Service...");
    const publisher = new MockEventPublisher();
    const ingestUseCase = new IngestClaimUseCase_js_1.IngestClaimUseCase(publisher);
    // Ingest sample claim schema
    const result = await ingestUseCase.execute({
        tenantId: "tenant_acme_health",
        sourceSystem: "EPIC_EHR_R4",
        format: "FHIR_R4",
        payload: {
            resourceType: "Claim",
            status: "active",
            type: { coding: [{ code: "institutional" }] },
            patient: { reference: "Patient/1001" },
            provider: { reference: "Organization/501" }
        }
    });
    logger.info("Ingestion test result", { result });
    logger.info("Ingestion Service listening on port 3002.");
}
bootstrap().catch(err => {
    logger.error("Failed to start ingestion-service", { error: err.message });
});
//# sourceMappingURL=index.js.map