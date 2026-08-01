import { AsyncLocalStorage } from "async_hooks";

export interface ITenantContext {
  tenantId: string;
  tenantName?: string;
  isolationMode: "SCHEMA_PER_TENANT" | "ROW_LEVEL_SECURITY" | "DATABASE_PER_TENANT";
  schemaOrDbName: string;
}

const tenantStorage = new AsyncLocalStorage<ITenantContext>();

export class TenantContextHolder {
  public static run<T>(context: ITenantContext, fn: () => T): T {
    return tenantStorage.run(context, fn);
  }

  public static getContext(): ITenantContext {
    const ctx = tenantStorage.getStore();
    if (!ctx) {
      throw new Error("TenantContext missing! Request executed outside tenant context boundary.");
    }
    return ctx;
  }

  public static getTenantId(): string {
    return TenantContextHolder.getContext().tenantId;
  }
}

export interface ITenantDatabaseResolver<TConnection> {
  getConnectionForTenant(tenantId: string): Promise<TConnection>;
}
