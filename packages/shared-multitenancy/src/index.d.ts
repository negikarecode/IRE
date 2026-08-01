export interface ITenantContext {
    tenantId: string;
    tenantName?: string;
    isolationMode: "SCHEMA_PER_TENANT" | "ROW_LEVEL_SECURITY" | "DATABASE_PER_TENANT";
    schemaOrDbName: string;
}
export declare class TenantContextHolder {
    static run<T>(context: ITenantContext, fn: () => T): T;
    static getContext(): ITenantContext;
    static getTenantId(): string;
}
export interface ITenantDatabaseResolver<TConnection> {
    getConnectionForTenant(tenantId: string): Promise<TConnection>;
}
