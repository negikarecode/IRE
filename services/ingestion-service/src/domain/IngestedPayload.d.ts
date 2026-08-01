import { AggregateRoot } from "@ire/shared-domain";
export interface IngestedPayloadProps {
    tenantId: string;
    sourceSystem: string;
    format: "FHIR_R4" | "EDI_837" | "CUSTOM_JSON";
    rawContent: string;
    ingestedAt: Date;
}
export declare class IngestedPayloadAggregate extends AggregateRoot<string> {
    private props;
    constructor(id: string, props: IngestedPayloadProps);
    get tenantId(): string;
    get format(): string;
    get rawContent(): string;
    static create(id: string, tenantId: string, sourceSystem: string, format: IngestedPayloadProps["format"], rawContent: string): IngestedPayloadAggregate;
}
