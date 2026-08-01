import { AggregateRoot } from "@ire/shared-domain";

export interface TenantProps {
  name: string;
  slug: string;
  isolationStrategy: "SCHEMA_PER_TENANT" | "ROW_LEVEL_SECURITY" | "DATABASE_PER_TENANT";
  status: "ACTIVE" | "SUSPENDED" | "PROVISIONING";
  createdAt: Date;
}

export class TenantAggregate extends AggregateRoot<string> {
  private props: TenantProps;

  constructor(id: string, props: TenantProps) {
    super(id);
    this.props = props;
  }

  get name(): string { return this.props.name; }
  get slug(): string { return this.props.slug; }
  get isolationStrategy(): string { return this.props.isolationStrategy; }
  get status(): string { return this.props.status; }

  public static create(id: string, name: string, slug: string, isolationStrategy: TenantProps["isolationStrategy"]): TenantAggregate {
    const tenant = new TenantAggregate(id, {
      name,
      slug,
      isolationStrategy,
      status: "PROVISIONING",
      createdAt: new Date()
    });

    tenant.addDomainEvent({
      eventId: `evt_${Date.now()}`,
      occurredOn: new Date(),
      tenantId: id,
      aggregateId: id,
      eventType: "TenantCreatedEvent",
      payload: { name, slug, isolationStrategy }
    });

    return tenant;
  }

  public activate(): void {
    this.props.status = "ACTIVE";
  }
}
