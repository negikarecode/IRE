import { AggregateRoot } from "@ire/shared-domain";

export interface IngestedPayloadProps {
  tenantId: string;
  sourceSystem: string;
  format: "FHIR_R4" | "EDI_837" | "CUSTOM_JSON";
  rawContent: string;
  ingestedAt: Date;
}

export class IngestedPayloadAggregate extends AggregateRoot<string> {
  private props: IngestedPayloadProps;

  constructor(id: string, props: IngestedPayloadProps) {
    super(id);
    this.props = props;
  }

  get tenantId(): string { return this.props.tenantId; }
  get format(): string { return this.props.format; }
  get rawContent(): string { return this.props.rawContent; }

  public static create(id: string, tenantId: string, sourceSystem: string, format: IngestedPayloadProps["format"], rawContent: string): IngestedPayloadAggregate {
    const aggregate = new IngestedPayloadAggregate(id, {
      tenantId,
      sourceSystem,
      format,
      rawContent,
      ingestedAt: new Date()
    });

    aggregate.addDomainEvent({
      eventId: `evt_ingest_${Date.now()}`,
      occurredOn: new Date(),
      tenantId,
      aggregateId: id,
      eventType: "ClaimPayloadIngestedEvent",
      payload: { payloadId: id, format, sourceSystem }
    });

    return aggregate;
  }
}
