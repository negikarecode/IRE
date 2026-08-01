import { AggregateRoot } from "@ire/shared-domain";
import crypto from "crypto";

export interface AuditLogProps {
  tenantId: string;
  actorId: string;
  action: string;
  resource: string;
  resourceId: string;
  previousHash: string;
  currentHash: string;
  timestamp: Date;
  payload: Record<string, unknown>;
}

export class AuditLogAggregate extends AggregateRoot<string> {
  private props: AuditLogProps;

  constructor(id: string, props: AuditLogProps) {
    super(id);
    this.props = props;
  }

  get currentHash(): string { return this.props.currentHash; }

  public static create(
    id: string,
    tenantId: string,
    actorId: string,
    action: string,
    resource: string,
    resourceId: string,
    previousHash: string,
    payload: Record<string, unknown>
  ): AuditLogAggregate {
    const timestamp = new Date();
    const dataToHash = `${id}:${tenantId}:${actorId}:${action}:${resource}:${resourceId}:${previousHash}:${timestamp.toISOString()}:${JSON.stringify(payload)}`;
    const currentHash = crypto.createHash("sha256").update(dataToHash).digest("hex");

    return new AuditLogAggregate(id, {
      tenantId,
      actorId,
      action,
      resource,
      resourceId,
      previousHash,
      currentHash,
      timestamp,
      payload
    });
  }
}
