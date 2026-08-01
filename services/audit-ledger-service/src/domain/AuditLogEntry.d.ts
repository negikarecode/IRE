import { AggregateRoot } from "@ire/shared-domain";
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
export declare class AuditLogAggregate extends AggregateRoot<string> {
    private props;
    constructor(id: string, props: AuditLogProps);
    get currentHash(): string;
    static create(id: string, tenantId: string, actorId: string, action: string, resource: string, resourceId: string, previousHash: string, payload: Record<string, unknown>): AuditLogAggregate;
}
