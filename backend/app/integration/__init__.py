"""
Enterprise Integration Platform Package
Provides BaseConnector SDK, Authenticators (OAuth 2.0, API Key), Connectors (REST, SOAP, FHIR, Webhook),
Rate Limiting, Retries, Dead Letter Queue (DLQ), and Health Monitoring.
Every integration connector MUST inherit from BaseConnector.
Framework only — Zero hospital or insurer integrations hardcoded.
"""

from app.integration.base_connector import BaseConnector, IntegrationMessage, IntegrationResponse
from app.integration.auth_adapters import IAuthenticator, OAuth2Authenticator, APIKeyAuthenticator
from app.integration.connectors import (
    RESTConnector,
    SOAPConnector,
    FHIRConnector,
    WebhookConnector
)
from app.integration.rate_limiter import TokenBucketRateLimiter
from app.integration.dlq import dlq_manager, DeadLetterQueueManager, DLQRecord
from app.integration.monitoring import integration_monitoring, IntegrationMonitoring, ConnectorTelemetrySummary
from app.integration.registry import connector_registry, ConnectorRegistry

__all__ = [
    "BaseConnector",
    "IntegrationMessage",
    "IntegrationResponse",
    "IAuthenticator",
    "OAuth2Authenticator",
    "APIKeyAuthenticator",
    "RESTConnector",
    "SOAPConnector",
    "FHIRConnector",
    "WebhookConnector",
    "TokenBucketRateLimiter",
    "dlq_manager",
    "DeadLetterQueueManager",
    "DLQRecord",
    "integration_monitoring",
    "IntegrationMonitoring",
    "ConnectorTelemetrySummary",
    "connector_registry",
    "ConnectorRegistry"
]
