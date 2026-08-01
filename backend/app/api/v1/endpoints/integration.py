from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time

from app.core.dependencies import get_tenant_header
from app.integration.base_connector import IntegrationMessage
from app.integration.connectors import RESTConnector, SOAPConnector, FHIRConnector, WebhookConnector
from app.integration.registry import connector_registry
from app.integration.dlq import dlq_manager
from app.integration.monitoring import integration_monitoring

router = APIRouter()

class RegisterConnectorDTO(BaseModel):
    connector_id: str
    name: str
    protocol: str  # REST, SOAP, FHIR, WEBHOOK
    endpoint_url: str

class SendIntegrationMessageDTO(BaseModel):
    connector_id: str
    payload: Any
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, Any]] = {}

from app.core.exceptions import BadRequestException, NotFoundException

@router.post("/connectors/register", status_code=status.HTTP_201_CREATED)
async def register_connector(dto: RegisterConnectorDTO):
    proto = dto.protocol.upper()
    if proto == "REST":
        conn = RESTConnector(dto.connector_id, dto.name, dto.endpoint_url)
    elif proto == "SOAP":
        conn = SOAPConnector(dto.connector_id, dto.name, dto.endpoint_url)
    elif proto == "FHIR":
        conn = FHIRConnector(dto.connector_id, dto.name, dto.endpoint_url)
    elif proto == "WEBHOOK":
        conn = WebhookConnector(dto.connector_id, dto.name, dto.endpoint_url)
    else:
        raise BadRequestException(message=f"Unsupported protocol '{dto.protocol}'")

    await conn.connect()
    connector_registry.register(conn)
    return {
        "success": True,
        "message": "Connector registered successfully",
        "data": {"status": "REGISTERED", "connector_id": dto.connector_id, "protocol": proto}
    }

@router.get("/connectors", status_code=status.HTTP_200_OK)
async def list_connectors():
    connectors = connector_registry.list_connectors()
    data = [
        {
            "connector_id": c.connector_id,
            "name": c.name,
            "endpoint_url": c.endpoint_url,
            "is_connected": c.is_connected
        }
        for c in connectors
    ]
    return {
        "success": True,
        "message": "Connectors listed successfully",
        "data": data
    }

@router.post("/send", status_code=status.HTTP_200_OK)
async def send_message(
    body: SendIntegrationMessageDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    conn = connector_registry.get(body.connector_id)
    if not conn:
        raise NotFoundException(message=f"Connector '{body.connector_id}' not found.")

    msg = IntegrationMessage(
        message_id=f"msg_{int(time.time() * 1000)}",
        tenant_id=tenant_id,
        connector_id=body.connector_id,
        protocol=conn.__class__.__name__,
        payload=body.payload,
        headers=body.headers or {},
        params=body.params or {}
    )

    try:
        res = await conn.send(msg)
        if not res.success:
            dlq_id = dlq_manager.push(tenant_id, body.connector_id, msg, res.error_message or "Delivery failure", 1)
            return {
                "success": False,
                "message": "Delivery failed, queued in DLQ",
                "data": {"status": "FAILED_QUEUED_IN_DLQ", "dlq_id": dlq_id, "error": res.error_message}
            }
        return {
            "success": True,
            "message": "Message sent successfully",
            "data": res
        }
    except Exception as e:
        dlq_id = dlq_manager.push(tenant_id, body.connector_id, msg, str(e), 1)
        return {
            "success": False,
            "message": "Exception occurred, queued in DLQ",
            "data": {"status": "EXCEPTION_QUEUED_IN_DLQ", "dlq_id": dlq_id, "error": str(e)}
        }

@router.get("/dlq", status_code=status.HTTP_200_OK)
async def list_dlq(tenant_id: str = Depends(get_tenant_header)):
    records = dlq_manager.list_by_tenant(tenant_id)
    data = [
        {
            "dlq_id": r.dlq_id,
            "connector_id": r.connector_id,
            "error_reason": r.error_reason,
            "retry_count": r.retry_count,
            "failed_at": r.failed_at
        }
        for r in records
    ]
    return {
        "success": True,
        "message": "DLQ records retrieved successfully",
        "data": data
    }

@router.post("/dlq/{dlq_id}/replay", status_code=status.HTTP_200_OK)
async def replay_dlq_message(dlq_id: str, tenant_id: str = Depends(get_tenant_header)):
    record = dlq_manager.get(dlq_id)
    if not record or record.tenant_id != tenant_id:
        raise NotFoundException(message="DLQ record not found.")

    res = await dlq_manager.replay(dlq_id)
    if res.success:
        return {
            "success": True,
            "message": "DLQ message replayed successfully",
            "data": {"status": "REPLAYED_SUCCESSFULLY", "data": res.data}
        }
    return {
        "success": False,
        "message": "DLQ replay failed",
        "data": {"status": "REPLAY_FAILED", "error": res.error_message}
    }

@router.delete("/dlq/{dlq_id}", status_code=status.HTTP_200_OK)
async def remove_dlq_message(dlq_id: str, tenant_id: str = Depends(get_tenant_header)):
    record = dlq_manager.get(dlq_id)
    if not record or record.tenant_id != tenant_id:
        raise NotFoundException(message="DLQ record not found.")

    dlq_manager.remove(dlq_id)
    return {
        "success": True,
        "message": "DLQ message removed successfully",
        "data": {"status": "REMOVED", "dlq_id": dlq_id}
    }

@router.get("/monitoring/{connector_id}", status_code=status.HTTP_200_OK)
async def get_monitoring(connector_id: str):
    telemetry = integration_monitoring.get_status(connector_id)
    return {
        "success": True,
        "message": "Integration monitoring status retrieved successfully",
        "data": {
            "connector_id": telemetry.connector_id,
            "status": telemetry.status,
            "total_sent": telemetry.total_sent,
            "total_received": telemetry.total_received,
            "total_errors": telemetry.total_errors,
            "average_latency_ms": telemetry.average_latency_ms
        }
    }
