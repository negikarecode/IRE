"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WebhookDispatcher = void 0;
const shared_logger_1 = require("@ire/shared-logger");
const logger = new shared_logger_1.Logger({ serviceName: "notification-event-service" });
class WebhookDispatcher {
    async dispatch(webhookUrl, event) {
        logger.info("Dispatching Webhook event to tenant subscriber", {
            tenantId: event.tenantid,
            webhookUrl,
            eventType: event.type
        });
    }
}
exports.WebhookDispatcher = WebhookDispatcher;
async function bootstrap() {
    logger.info("Initializing Notification & Event Dispatcher Service...");
    const dispatcher = new WebhookDispatcher();
    await dispatcher.dispatch("https://api.acme-health.com/webhooks/ire", {
        specversion: "1.0",
        id: "evt_100",
        source: "ire/claim-lifecycle",
        type: "com.ire.claim.adjudicated.v1",
        subject: "claim_9001",
        time: new Date().toISOString(),
        datacontenttype: "application/json",
        tenantid: "tenant_acme_health",
        correlationid: "corr_100",
        data: { status: "ADJUDICATED", recommendation: "APPROVE" }
    });
    logger.info("Notification Event Service listening on port 3007.");
}
bootstrap().catch(err => {
    logger.error("Failed to start notification-event-service", { error: err.message });
});
//# sourceMappingURL=index.js.map