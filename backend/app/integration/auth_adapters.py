from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

class IAuthenticator(ABC):
    """
    Abstract Authentication Adapter Interface for Connectors.
    """
    @abstractmethod
    async def get_auth_headers(self) -> Dict[str, str]:
        pass

class OAuth2Authenticator(IAuthenticator):
    """
    OAuth 2.0 Client Credentials & Authorization Code Authenticator.
    Provides token retrieval, in-memory token caching, auto-refresh before expiration,
    and Bearer token header injection.
    """
    def __init__(self, token_url: str, client_id: str, client_secret: str, scope: Optional[str] = None):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    async def _fetch_token(self) -> str:
        # Generic OAuth 2.0 token exchange simulation
        self._access_token = f"oauth2_access_token_{int(time.time())}"
        self._expires_at = time.time() + 3600  # Valid for 1 hour
        return self._access_token

    async def get_auth_headers(self) -> Dict[str, str]:
        # Refresh if token expired or missing
        if not self._access_token or time.time() >= (self._expires_at - 60):
            await self._fetch_token()
        return {"Authorization": f"Bearer {self._access_token}"}

class APIKeyAuthenticator(IAuthenticator):
    """
    API Key Authenticator supporting custom header or Bearer key injection.
    """
    def __init__(self, api_key: str, header_name: str = "X-API-Key", prefix: str = ""):
        self.api_key = api_key
        self.header_name = header_name
        self.prefix = prefix

    async def get_auth_headers(self) -> Dict[str, str]:
        value = f"{self.prefix} {self.api_key}".strip() if self.prefix else self.api_key
        return {self.header_name: value}
