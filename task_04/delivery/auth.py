from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import aiohttp

USERS_SERVICE_URL = "http://users-service:8082"

security = HTTPBearer()


async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{USERS_SERVICE_URL}/validate-token", 
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                user_data = await response.json()
                return int(user_data.get("user_id"))
    except aiohttp.ClientError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


async def get_current_user(user_id: int = Depends(validate_token)):
    return user_id
