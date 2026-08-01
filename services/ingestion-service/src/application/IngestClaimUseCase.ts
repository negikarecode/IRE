import { IngestedPayloadAggregate } from "../domain/IngestedPayload.js";
import { CloudEvent, IEventPublisher } from "@ire/shared-events";
import { ValidationException } from "@ire/shared-errors";

export interface IngestClaimDTO {
  tenantId: string;
  sourceSystem: string;
  format: "FHIR_R4" | "EDI_837" | "CUSTOM_JSON";
  payload: Record<string, unknown>;
}

export class IngestClaimUseCase {
  constructor(private eventPublisher: IEventPublisher) {}

  public async execute(dto: IngestClaimDTO): Promise<{ payloadId: string; status: string }> {
    if (!dto.payload || Object.keys(dto.payload).length === 0) {
      throw new ValidationException("Ingestion payload cannot be empty");
    }

    const payloadId = `ing_${Date.now()}`;
    const rawContent = JSON.stringify(dto.payload);

    const aggregate = IngestedPayloadAggregate.create(
      payloadId,
      dto.tenantId,
      dto.sourceSystem,
      dto.format,
      rawContent
    );

    // Emit CloudEvent to event bus
    const event: CloudEvent = {
      specversion: "1.0",
      id: `evt_${Date.now()}`,
      source: "ire/ingestion-service",
      type: "com.ire.claim.ingested.v1",
      subject: payloadId,
      time: new Date().toISOString(),
      datacontenttype: "application/json",
      tenantid: dto.tenantId,
      correlationid: `corr_${Date.now()}`,
      data: {
        payloadId,
        format: dto.format,
        sourceSystem: dto.sourceSystem,
        rawPayload: dto.payload
      }
    };

    await this.eventPublisher.publish(event);

    return { payloadId, status: "ACCEPTED" };
  }
}
