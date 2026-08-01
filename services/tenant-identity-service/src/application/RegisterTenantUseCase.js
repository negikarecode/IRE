"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RegisterTenantUseCase = void 0;
const Tenant_js_1 = require("../domain/Tenant.js");
const shared_errors_1 = require("@ire/shared-errors");
class RegisterTenantUseCase {
    tenantRepo;
    constructor(tenantRepo) {
        this.tenantRepo = tenantRepo;
    }
    async execute(dto) {
        const existing = await this.tenantRepo.findBySlug(dto.slug);
        if (existing) {
            throw new shared_errors_1.ValidationException(`Tenant with slug '${dto.slug}' already exists`);
        }
        const tenant = Tenant_js_1.TenantAggregate.create(dto.tenantId, dto.name, dto.slug, dto.isolationStrategy);
        tenant.activate();
        await this.tenantRepo.save(tenant);
        return { id: tenant.id, status: tenant.status };
    }
}
exports.RegisterTenantUseCase = RegisterTenantUseCase;
//# sourceMappingURL=RegisterTenantUseCase.js.map