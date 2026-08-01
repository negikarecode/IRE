import { Logger } from "@ire/shared-logger";
import { TenantAccessDeniedException } from "@ire/shared-errors";

const logger = new Logger({ serviceName: "api-gateway" });

export class ApiGatewayRouter {
  public routeRequest(path: string, headers: Record<string, string>): { serviceTarget: string; tenantId: string } {
    const tenantId = headers["x-tenant-id"];
    if (!tenantId) {
      throw new TenantAccessDeniedException("Missing mandatory 'X-Tenant-ID' request header.");
    }

    let serviceTarget = "unknown";
    if (path.startsWith("/api/v1/tenants")) serviceTarget = "http://tenant-identity-service:3001";
    else if (path.startsWith("/api/v1/ingest")) serviceTarget = "http://ingestion-service:3002";
    else if (path.startsWith("/api/v1/claims")) serviceTarget = "http://claim-lifecycle-service:3003";
    else if (path.startsWith("/api/v1/reasoning")) serviceTarget = "http://reasoning-engine-service:3004";
    else if (path.startsWith("/api/v1/agents")) serviceTarget = "http://ai-agent-service:3005";
    else if (path.startsWith("/api/v1/audit")) serviceTarget = "http://audit-ledger-service:3006";

    return { serviceTarget, tenantId };
  }
}

async function bootstrap() {
  logger.info("Initializing API Gateway Edge Router...");
  const router = new ApiGatewayRouter();

  const route = router.routeRequest("/api/v1/claims/claim_9001", { "x-tenant-id": "tenant_acme_health" });
  logger.info("Routed incoming request successfully", route);
  logger.info("API Gateway running on port 8000.");
}

bootstrap().catch(err => {
  logger.error("API Gateway execution error", { error: err.message });
});
