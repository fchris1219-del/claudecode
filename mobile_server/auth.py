from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from mobile_server.config import settings

_bearer = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(_bearer)) -> None:
    if credentials.credentials != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
