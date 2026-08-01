from typing import Dict, List, Optional
from app.integration.base_connector import BaseConnector
from app.integration.connectors import RESTConnector, SOAPConnector, FHIRConnector, WebhookConnector

class ConnectorRegistry:
    """
    Central Registry for managing active enterprise connectors.
    CRITICAL: Enforces that ALL registered connectors MUST inherit from BaseConnector.
    """
    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._seed_default_connectors()

    def _seed_default_connectors(self):
        self.register(RESTConnector("rest_generic", "Generic REST API Connector", "https://api.example.com/v1"))
        self.register(SOAPConnector("soap_generic", "Generic SOAP Web Service", "https://api.example.com/soap"))
        self.register(FHIRConnector("fhir_generic", "Generic FHIR R4 API Connector", "https://fhir.example.org/r4"))
        self.register(WebhookConnector("webhook_generic", "Generic Webhook Connector", "https://api.example.com/webhook"))

    def register(self, connector: BaseConnector) -> None:
        if not isinstance(connector, BaseConnector):
            raise TypeError("All integration connectors MUST inherit from BaseConnector!")
        self._connectors[connector.connector_id] = connector

    def unregister(self, connector_id: str) -> bool:
        if connector_id in self._connectors:
            del self._connectors[connector_id]
            return True
        return False

    def get(self, connector_id: str) -> Optional[BaseConnector]:
        return self._connectors.get(connector_id)

    def list_connectors(self) -> List[BaseConnector]:
        return list(self._connectors.values())

connector_registry = ConnectorRegistry()
