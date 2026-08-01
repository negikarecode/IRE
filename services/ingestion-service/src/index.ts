import { Logger } from "@ire/shared-logger";
import { IngestClaimUseCase } from "./application/IngestClaimUseCase.js";
import { CloudEvent, IEventPublisher } from "@ire/shared-events";

const logger = new Logger({ serviceName: "ingestion-service" });

class MockEventPublisher implements IEventPublisher {
  public async publish<T>(event: CloudEvent<T>): Promise<void> {
    logger.info("Published CloudEvent to Kafka/RabbitMQ", { eventId: event.id, type: event.type, tenant: event.tenantid });
  }
  public async publishBatch<T>(events: CloudEvent<T>[]): Promise<void> {
    for (const e of events) await this.publish(e);
  }
}

async function bootstrap() {
  logger.info("Initializing Ingestion & EHR Integration Service...");
  const publisher = new MockEventPublisher();
  const ingestUseCase = new IngestClaimUseCase(publisher);

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
