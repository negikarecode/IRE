"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const shared_logger_1 = require("@ire/shared-logger");
const RegisterTenantUseCase_js_1 = require("./application/RegisterTenantUseCase.js");
const PostgresTenantRepository_js_1 = require("./infrastructure/PostgresTenantRepository.js");
const logger = new shared_logger_1.Logger({ serviceName: "tenant-identity-service" });
async function bootstrap() {
    logger.info("Initializing Tenant & Identity Service...");
    const tenantRepo = new PostgresTenantRepository_js_1.PostgresTenantRepository();
    const registerUseCase = new RegisterTenantUseCase_js_1.RegisterTenantUseCase(tenantRepo);
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
//# sourceMappingURL=index.js.map