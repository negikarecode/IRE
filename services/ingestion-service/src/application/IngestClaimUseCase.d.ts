import { IEventPublisher } from "@ire/shared-events";
export interface IngestClaimDTO {
    tenantId: string;
    sourceSystem: string;
    format: "FHIR_R4" | "EDI_837" | "CUSTOM_JSON";
    payload: Record<string, unknown>;
}
export declare class IngestClaimUseCase {
    private eventPublisher;
    constructor(eventPublisher: IEventPublisher);
    execute(dto: IngestClaimDTO): Promise<{
        payloadId: string;
        status: string;
    }>;
}
