from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from .supabase_client import auth_client, admin_client

async def get_current_user(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        result = auth_client.auth.get_user(token)
        user = result.user
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from exc
    if not user:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return user

async def get_profile(user=Depends(get_current_user)):
    result = admin_client.table("profiles").select("*").eq("id", str(user.id)).single().execute()
    if not result.data:
        raise HTTPException(status_code=403, detail="Profile not provisioned")
    return result.data

def require_role(*roles: str):
    async def dependency(profile=Depends(get_profile)):
        if profile["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return profile
    return dependency
