import { ITenantRepository } from "../domain/ITenantRepository.js";
export interface RegisterTenantDTO {
    tenantId: string;
    name: string;
    slug: string;
    isolationStrategy: "SCHEMA_PER_TENANT" | "ROW_LEVEL_SECURITY" | "DATABASE_PER_TENANT";
}
export declare class RegisterTenantUseCase {
    private tenantRepo;
    constructor(tenantRepo: ITenantRepository);
    execute(dto: RegisterTenantDTO): Promise<{
        id: string;
        status: string;
    }>;
}
