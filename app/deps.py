# app/deps.py
# FastAPI dependencies for authentication & admin checks.

from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from jose.exceptions import JWTError
from .utils.auth import verify_supabase_jwt
from app.supabase_client import supabase  # service-role client (server-only)

async def get_bearer_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return authorization.split(" ", 1)[1].strip()


async def get_current_user(token: str = Depends(get_bearer_token)) -> Dict[str, Any]:
    """
    Verifies the Supabase JWT and returns a simple user dict:
    { "id": <sub>, "claims": <raw claims> }
    """
    try:
        claims = await verify_supabase_jwt(token)
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing 'sub' claim")

    return {"id": user_id, "claims": claims}


async def get_current_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Ensures the authenticated user has an admin/staff role.
    Looks up profiles table using the service-role supabase client.
    Returns the enriched profile row (if any).
    """
    user_id = user["id"]
    # Query profiles table for role / is_admin. This uses service-role key (server-side)
    resp = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    # resp shape can vary by supabase client version; handle both dict/object
    profile = None
    if isinstance(resp, dict):
        if resp.get("error"):
            profile = None
        else:
            # data may be list or single
            profile = resp.get("data")
            if isinstance(profile, list) and profile:
                profile = profile[0]
    else:
        # object-like response
        profile = getattr(resp, "data", None)
    if not profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile not found")

    role = profile.get("role") or profile.get("role", "").lower()
    allowed = {"admin", "staff", "department_head"}
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    # attach profile to returned object
    user["profile"] = profile
    return user
