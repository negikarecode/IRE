import { ITenantRepository } from "../domain/ITenantRepository.js";
import { TenantAggregate } from "../domain/Tenant.js";
export declare class PostgresTenantRepository implements ITenantRepository {
    private inMemoryStore;
    findById(id: string): Promise<TenantAggregate | null>;
    findBySlug(slug: string): Promise<TenantAggregate | null>;
    save(tenant: TenantAggregate): Promise<void>;
}
