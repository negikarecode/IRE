"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PostgresTenantRepository = void 0;
class PostgresTenantRepository {
    inMemoryStore = new Map();
    async findById(id) {
        return this.inMemoryStore.get(id) || null;
    }
    async findBySlug(slug) {
        for (const tenant of this.inMemoryStore.values()) {
            if (tenant.slug === slug)
                return tenant;
        }
        return null;
    }
    async save(tenant) {
        this.inMemoryStore.set(tenant.id, tenant);
        // In production, persists to PostgreSQL ire_tenant_db using knex / prisma / raw pg client
    }
}
exports.PostgresTenantRepository = PostgresTenantRepository;
//# sourceMappingURL=PostgresTenantRepository.js.map