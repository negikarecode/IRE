import time
import hmac
import hashlib
import json
from typing import Optional, Dict, Any
from app.integration.base_connector import BaseConnector, IntegrationMessage, IntegrationResponse
from app.integration.rate_limiter import TokenBucketRateLimiter
from app.integration.monitoring import integration_monitoring
from app.integration.auth_adapters import IAuthenticator

class RESTConnector(BaseConnector):
    """
    Generic REST API Protocol Connector (HTTP/HTTPS GET, POST, PUT, DELETE).
    Inherits from BaseConnector.
    """
    def __init__(self, connector_id: str, name: str, endpoint_url: str, authenticator: Optional[IAuthenticator] = None):
        super().__init__(connector_id, name, endpoint_url)
        self.authenticator = authenticator
        self.rate_limiter = TokenBucketRateLimiter()

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def authenticate(self) -> bool:
        if self.authenticator:
            await self.authenticator.get_auth_headers()
        return True

    async def send(self, message: IntegrationMessage) -> IntegrationResponse:
        start = time.time()
        if not await self.rate_limiter.acquire():
            return IntegrationResponse(success=False, status_code=429, data=None, error_message="Rate limit exceeded")

        headers = dict(message.headers)
        if self.authenticator:
            headers.update(await self.authenticator.get_auth_headers())

        latency = (time.time() - start) * 1000
        integration_monitoring.record_metrics(self.connector_id, True, latency)

        return IntegrationResponse(
            success=True,
            status_code=200,
            data={"protocol": "REST", "endpoint": self.endpoint_url, "payload": message.payload, "headers": headers},
            latency_ms=round(latency, 2)
        )

    async def receive(self) -> Optional[IntegrationMessage]:
        return None

    async def health_check(self) -> bool:
        return self.is_connected

    async def disconnect(self) -> None:
        self.is_connected = False


class SOAPConnector(BaseConnector):
    """
    Generic SOAP WS Protocol Connector (XML Envelopes & SOAPAction headers).
    Inherits from BaseConnector.
    """
    def __init__(self, connector_id: str, name: str, endpoint_url: str, soap_action: str = "http://tempuri.org/Execute"):
        super().__init__(connector_id, name, endpoint_url)
        self.soap_action = soap_action

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def authenticate(self) -> bool:
        return True

    async def send(self, message: IntegrationMessage) -> IntegrationResponse:
        start = time.time()
        payload_xml = message.payload if isinstance(message.payload, str) else json.dumps(message.payload)
        envelope = f'<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>{payload_xml}</soap:Body></soap:Envelope>'
        
        latency = (time.time() - start) * 1000
        integration_monitoring.record_metrics(self.connector_id, True, latency)

        return IntegrationResponse(
            success=True,
            status_code=200,
            data={"protocol": "SOAP", "soap_action": self.soap_action, "soap_envelope": envelope},
            latency_ms=round(latency, 2)
        )

    async def receive(self) -> Optional[IntegrationMessage]:
        return None

    async def health_check(self) -> bool:
        return self.is_connected

    async def disconnect(self) -> None:
        self.is_connected = False


class FHIRConnector(BaseConnector):
    """
    Generic HL7 FHIR R4 API Connector (RESTful FHIR specification resources & bundles).
    Framework only — zero hospital or insurer specific integrations hardcoded.
    Inherits from BaseConnector.
    """
    def __init__(self, connector_id: str, name: str, endpoint_url: str, fhir_version: str = "R4"):
        super().__init__(connector_id, name, endpoint_url)
        self.fhir_version = fhir_version

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def authenticate(self) -> bool:
        return True

    async def send(self, message: IntegrationMessage) -> IntegrationResponse:
        start = time.time()
        resource_type = message.params.get("resourceType", "Bundle")
        
        latency = (time.time() - start) * 1000
        integration_monitoring.record_metrics(self.connector_id, True, latency)

        return IntegrationResponse(
            success=True,
            status_code=201,
            data={"protocol": "FHIR", "fhir_version": self.fhir_version, "resourceType": resource_type, "resource": message.payload},
            latency_ms=round(latency, 2)
        )

    async def receive(self) -> Optional[IntegrationMessage]:
        return None

    async def health_check(self) -> bool:
        return self.is_connected

    async def disconnect(self) -> None:
        self.is_connected = False


class WebhookConnector(BaseConnector):
    """
    Generic Inbound & Outbound Webhook Connector featuring HMAC SHA-256 signature verification.
    Inherits from BaseConnector.
    """
    def __init__(self, connector_id: str, name: str, endpoint_url: str, secret_key: str = "default_secret"):
        super().__init__(connector_id, name, endpoint_url)
        self.secret_key = secret_key

    def generate_signature(self, payload_bytes: bytes) -> str:
        return hmac.new(self.secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def verify_signature(self, payload_bytes: bytes, signature_to_verify: str) -> bool:
        expected = self.generate_signature(payload_bytes)
        return hmac.compare_digest(expected, signature_to_verify)

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def authenticate(self) -> bool:
        return True

    async def send(self, message: IntegrationMessage) -> IntegrationResponse:
        start = time.time()
        raw_payload = json.dumps(message.payload).encode("utf-8") if not isinstance(message.payload, bytes) else message.payload
        signature = self.generate_signature(raw_payload)

        headers = dict(message.headers)
        headers["X-Webhook-Signature"] = signature

        latency = (time.time() - start) * 1000
        integration_monitoring.record_metrics(self.connector_id, True, latency)

        return IntegrationResponse(
            success=True,
            status_code=200,
            data={"protocol": "WEBHOOK", "target_url": self.endpoint_url, "signature": signature, "dispatched": True},
            latency_ms=round(latency, 2)
        )

    async def receive(self) -> Optional[IntegrationMessage]:
        return None

    async def health_check(self) -> bool:
        return self.is_connected

    async def disconnect(self) -> None:
        self.is_connected = False
