import pytest
import asyncio

from app.integration.base_connector import BaseConnector, IntegrationMessage, IntegrationResponse
from app.integration.auth_adapters import OAuth2Authenticator, APIKeyAuthenticator
from app.integration.connectors import RESTConnector, SOAPConnector, FHIRConnector, WebhookConnector
from app.integration.registry import connector_registry, ConnectorRegistry
from app.integration.dlq import dlq_manager, DLQRecord
from app.integration.monitoring import integration_monitoring
from app.integration.rate_limiter import TokenBucketRateLimiter

def run_async(coro):
    return asyncio.run(coro)

# 1. Test BaseConnector SDK Inheritance Enforcement
def test_connector_sdk_inheritance_enforcement():
    class CustomGoodConnector(BaseConnector):
        async def connect(self) -> bool: return True
        async def authenticate(self) -> bool: return True
        async def send(self, message: IntegrationMessage) -> IntegrationResponse:
            return IntegrationResponse(success=True, status_code=200, data={"ok": True})
        async def receive(self): return None
        async def health_check(self) -> bool: return True
        async def disconnect(self): pass

    reg = ConnectorRegistry()

    # Valid connector inheriting from BaseConnector
    good_conn = CustomGoodConnector("conn_good", "Good Connector", "https://api.example.com")
    reg.register(good_conn)
    assert reg.get("conn_good") is not None

    # Invalid connector NOT inheriting from BaseConnector
    class InvalidFakeConnector:
        pass

    with pytest.raises(TypeError) as exc_info:
        reg.register(InvalidFakeConnector())
    assert "MUST inherit from BaseConnector" in str(exc_info.value)

# 2. Test Authenticators (OAuth2 & API Keys)
def test_authenticators():
    async def _test():
        # OAuth2 Token Exchange & Bearer injection
        oauth = OAuth2Authenticator(token_url="https://auth.example.com/oauth/token", client_id="c123", client_secret="secret")
        headers = await oauth.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer oauth2_access_token_")

        # API Key Authenticator
        api_key_auth = APIKeyAuthenticator(api_key="secret_key_999", header_name="X-API-Key")
        key_headers = await api_key_auth.get_auth_headers()
        assert key_headers["X-API-Key"] == "secret_key_999"

    run_async(_test())

# 3. Test REST Connector
def test_rest_connector():
    async def _test():
        auth = APIKeyAuthenticator(api_key="rest_key_101")
        conn = RESTConnector("rest_test", "REST Test Endpoint", "https://api.example.com/v1/resource", authenticator=auth)
        await conn.connect()

        msg = IntegrationMessage(
            message_id="msg_rest_1",
            tenant_id="tenant_a",
            connector_id="rest_test",
            protocol="REST",
            payload={"param": "value"}
        )
        res = await conn.send(msg)

        assert res.success is True
        assert res.status_code == 200
        assert res.data["headers"]["X-API-Key"] == "rest_key_101"

    run_async(_test())

# 4. Test SOAP Connector
def test_soap_connector():
    async def _test():
        conn = SOAPConnector("soap_test", "SOAP Test Endpoint", "https://api.example.com/soap")
        await conn.connect()

        msg = IntegrationMessage(
            message_id="msg_soap_1",
            tenant_id="tenant_a",
            connector_id="soap_test",
            protocol="SOAP",
            payload="<GetUserRequest><UserId>12345</UserId></GetUserRequest>"
        )
        res = await conn.send(msg)

        assert res.success is True
        assert "<soap:Envelope" in res.data["soap_envelope"]
        assert "<UserId>12345</UserId>" in res.data["soap_envelope"]

    run_async(_test())

# 5. Test FHIR Connector (Framework standard JSON resource, zero hospital logic)
def test_fhir_connector():
    async def _test():
        conn = FHIRConnector("fhir_test", "FHIR R4 Endpoint", "https://fhir.example.org/r4")
        await conn.connect()

        msg = IntegrationMessage(
            message_id="msg_fhir_1",
            tenant_id="tenant_b",
            connector_id="fhir_test",
            protocol="FHIR",
            payload={"resourceType": "Parameters", "parameter": [{"name": "eval", "valueString": "test"}]},
            params={"resourceType": "Parameters"}
        )
        res = await conn.send(msg)

        assert res.success is True
        assert res.status_code == 201
        assert res.data["resourceType"] == "Parameters"

    run_async(_test())

# 6. Test Webhook Connector & HMAC Signature Verification
def test_webhook_connector_hmac():
    async def _test():
        conn = WebhookConnector("wh_test", "Webhook Dispatcher", "https://webhook.site/receiver", secret_key="my_super_secret")
        await conn.connect()

        raw_payload = b'{"event": "user.signup", "user_id": 42}'
        signature = conn.generate_signature(raw_payload)
        
        # Verify signature
        assert conn.verify_signature(raw_payload, signature) is True
        assert conn.verify_signature(raw_payload, "invalid_sig") is False

        # Send webhook message
        msg = IntegrationMessage(
            message_id="msg_wh_1",
            tenant_id="tenant_c",
            connector_id="wh_test",
            protocol="WEBHOOK",
            payload={"event": "user.signup", "user_id": 42}
        )
        res = await conn.send(msg)

        assert res.success is True
        assert res.data["signature"] is not None

    run_async(_test())

# 7. Test Dead Letter Queue (DLQ) Push & Replay
def test_dead_letter_queue():
    async def _test():
        # Setup REST connector in registry for replay
        conn = RESTConnector("conn_dlq_test", "DLQ Test Connector", "https://api.example.com")
        await conn.connect()
        connector_registry.register(conn)

        msg = IntegrationMessage(
            message_id="msg_failed_1",
            tenant_id="tenant_dlq",
            connector_id="conn_dlq_test",
            protocol="REST",
            payload={"retry": "data"}
        )

        # Push to DLQ
        dlq_id = dlq_manager.push("tenant_dlq", "conn_dlq_test", msg, error_reason="HTTP 503 Service Unavailable", retry_count=3)
        assert dlq_id is not None

        dlq_records = dlq_manager.list_by_tenant("tenant_dlq")
        assert len(dlq_records) >= 1

        # Replay message from DLQ
        replay_res = await dlq_manager.replay(dlq_id)
        assert replay_res.success is True

        # DLQ record should be removed after successful replay
        assert dlq_manager.get(dlq_id) is None

    run_async(_test())

# 8. Test Integration Monitoring
def test_integration_monitoring():
    integration_monitoring.record_metrics("conn_mon_test", success=True, latency_ms=15.5)
    integration_monitoring.record_metrics("conn_mon_test", success=True, latency_ms=20.0)

    status = integration_monitoring.get_status("conn_mon_test")
    assert status.status == "HEALTHY"
    assert status.total_sent >= 2
    assert status.average_latency_ms > 0.0
