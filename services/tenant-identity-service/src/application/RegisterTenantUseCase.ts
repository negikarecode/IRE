import { TenantAggregate } from "../domain/Tenant.js";
import { ITenantRepository } from "../domain/ITenantRepository.js";
import { ValidationException } from "@ire/shared-errors";

export interface RegisterTenantDTO {
  tenantId: string;
  name: string;
  slug: string;
  isolationStrategy: "SCHEMA_PER_TENANT" | "ROW_LEVEL_SECURITY" | "DATABASE_PER_TENANT";
}

export class RegisterTenantUseCase {
  constructor(private tenantRepo: ITenantRepository) {}

  public async execute(dto: RegisterTenantDTO): Promise<{ id: string; status: string }> {
    const existing = await this.tenantRepo.findBySlug(dto.slug);
    if (existing) {
      throw new ValidationException(`Tenant with slug '${dto.slug}' already exists`);
    }

    const tenant = TenantAggregate.create(dto.tenantId, dto.name, dto.slug, dto.isolationStrategy);
    tenant.activate();

    await this.tenantRepo.save(tenant);
    return { id: tenant.id, status: tenant.status };
  }
}
