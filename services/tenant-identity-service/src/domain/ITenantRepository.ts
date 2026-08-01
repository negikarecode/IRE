import { TenantAggregate } from "./Tenant.js";

export interface ITenantRepository {
  findById(id: string): Promise<TenantAggregate | null>;
  findBySlug(slug: string): Promise<TenantAggregate | null>;
  save(tenant: TenantAggregate): Promise<void>;
}
