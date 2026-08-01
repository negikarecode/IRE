from abc import ABC, abstractmethod
from typing import Dict, Any, BinaryIO

class IStorageService(ABC):
    @abstractmethod
    async def upload_file(self, tenant_id: str, file_name: str, file_obj: BinaryIO, content_type: str) -> str:
        pass

    @abstractmethod
    async def get_file_url(self, tenant_id: str, file_path: str) -> str:
        pass

class INotificationService(ABC):
    @abstractmethod
    async def send_notification(self, tenant_id: str, recipient_id: str, channel: str, message: str, payload: Dict[str, Any] = None) -> bool:
        pass

class IAuditService(ABC):
    @abstractmethod
    async def log_action(self, tenant_id: str, actor_id: str, action: str, resource: str, resource_id: str, details: Dict[str, Any]) -> None:
        pass
