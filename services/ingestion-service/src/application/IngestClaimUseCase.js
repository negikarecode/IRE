"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IngestClaimUseCase = void 0;
const IngestedPayload_js_1 = require("../domain/IngestedPayload.js");
const shared_errors_1 = require("@ire/shared-errors");
class IngestClaimUseCase {
    eventPublisher;
    constructor(eventPublisher) {
        this.eventPublisher = eventPublisher;
    }
    async execute(dto) {
        if (!dto.payload || Object.keys(dto.payload).length === 0) {
            throw new shared_errors_1.ValidationException("Ingestion payload cannot be empty");
        }
        const payloadId = `ing_${Date.now()}`;
        const rawContent = JSON.stringify(dto.payload);
        const aggregate = IngestedPayload_js_1.IngestedPayloadAggregate.create(payloadId, dto.tenantId, dto.sourceSystem, dto.format, rawContent);
        // Emit CloudEvent to event bus
        const event = {
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
exports.IngestClaimUseCase = IngestClaimUseCase;
//# sourceMappingURL=IngestClaimUseCase.js.map