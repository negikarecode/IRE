from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.exceptions import BadRequestException
from app.sdk.registry import plugin_registry
from app.sdk.discovery import plugin_discovery_engine

router = APIRouter()

class ExecutePluginDTO(BaseModel):
    extension_point: str
    plugin_id: str
    method_name: str
    kwargs: Optional[Dict[str, Any]] = {}

@router.post("/plugins/discover", status_code=status.HTTP_200_OK)
async def discover_plugins():
    res = plugin_discovery_engine.discover_and_load()
    return {
        "success": True,
        "message": "Plugins discovered successfully",
        "data": res
    }

@router.get("/plugins", status_code=status.HTTP_200_OK)
async def list_plugins(extension_point: Optional[str] = None):
    plugins = plugin_registry.list_plugins(extension_point)
    data = [
        {
            "plugin_id": p.plugin_id,
            "name": p.name,
            "version": p.version,
            "author": p.author,
            "description": p.description,
            "extension_point": p.extension_point,
            "enabled": p.enabled,
            "created_at": p.created_at
        }
        for p in plugins
    ]
    return {
        "success": True,
        "message": "Plugins listed successfully",
        "data": data
    }

@router.post("/plugins/execute", status_code=status.HTTP_200_OK)
async def execute_plugin(dto: ExecutePluginDTO):
    try:
        res = await plugin_registry.execute(
            extension_point=dto.extension_point,
            plugin_id=dto.plugin_id,
            method_name=dto.method_name,
            **(dto.kwargs or {})
        )
        return {
            "success": True,
            "message": "Plugin executed successfully",
            "data": {"status": "SUCCESS", "extension_point": dto.extension_point, "plugin_id": dto.plugin_id, "result": res}
        }
    except Exception as e:
        raise BadRequestException(message=str(e))
