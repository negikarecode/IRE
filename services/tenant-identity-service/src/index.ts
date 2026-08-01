import { Logger } from "@ire/shared-logger";
import { RegisterTenantUseCase } from "./application/RegisterTenantUseCase.js";
import { PostgresTenantRepository } from "./infrastructure/PostgresTenantRepository.js";

const logger = new Logger({ serviceName: "tenant-identity-service" });

async function bootstrap() {
  logger.info("Initializing Tenant & Identity Service...");
  
  const tenantRepo = new PostgresTenantRepository();
  const registerUseCase = new RegisterTenantUseCase(tenantRepo);

  // Seed sample enterprise tenant
  const tenant = await registerUseCase.execute({
    tenantId: "tenant_acme_health",
    name: "Acme Health Insurance",
    slug: "acme-health",
    isolationStrategy: "SCHEMA_PER_TENANT"
  });

  logger.info("Registered initial tenant", { tenant });
  logger.info("Tenant & Identity Service running on port 3001.");
}

bootstrap().catch(err => {
  logger.error("Failed to start tenant-identity-service", { error: err.message });
});
