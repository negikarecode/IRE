import { ITenantRepository } from "../domain/ITenantRepository.js";
import { TenantAggregate } from "../domain/Tenant.js";

export class PostgresTenantRepository implements ITenantRepository {
  private inMemoryStore = new Map<string, TenantAggregate>();

  public async findById(id: string): Promise<TenantAggregate | null> {
    return this.inMemoryStore.get(id) || null;
  }

  public async findBySlug(slug: string): Promise<TenantAggregate | null> {
    for (const tenant of this.inMemoryStore.values()) {
      if (tenant.slug === slug) return tenant;
    }
    return null;
  }

  public async save(tenant: TenantAggregate): Promise<void> {
    this.inMemoryStore.set(tenant.id, tenant);
    // In production, persists to PostgreSQL ire_tenant_db using knex / prisma / raw pg client
  }
}
