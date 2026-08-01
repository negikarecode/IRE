import { AggregateRoot } from "@ire/shared-domain";
export interface TenantProps {
    name: string;
    slug: string;
    isolationStrategy: "SCHEMA_PER_TENANT" | "ROW_LEVEL_SECURITY" | "DATABASE_PER_TENANT";
    status: "ACTIVE" | "SUSPENDED" | "PROVISIONING";
    createdAt: Date;
}
export declare class TenantAggregate extends AggregateRoot<string> {
    private props;
    constructor(id: string, props: TenantProps);
    get name(): string;
    get slug(): string;
    get isolationStrategy(): string;
    get status(): string;
    static create(id: string, name: string, slug: string, isolationStrategy: TenantProps["isolationStrategy"]): TenantAggregate;
    activate(): void;
}
