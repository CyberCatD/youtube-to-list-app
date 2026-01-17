from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from .config import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

VALID_API_KEYS = set(settings.api_keys_list)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not VALID_API_KEYS:
        return None
    
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return api_key
