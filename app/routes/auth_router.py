# app/routes/auth_router.py
# Router exposing /auth/me and an admin-only helper to create admin profile entries.
# NOTE: Creating admin accounts should be a protected manual action. This route
# should be disabled or protected in production (or removed after use).

from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import get_current_user, get_current_admin
from pydantic import BaseModel
from app.supabase_client import supabase  # service-role client

router = APIRouter(prefix="/auth", tags=["auth"])

class CreateAdminIn(BaseModel):
    user_id: str  # auth.users.id (uuid)
    full_name: str | None = None
    role: str = "admin"  # admin | staff | department_head
    phone: str | None = None

@router.get("/me")
async def me(user = Depends(get_current_user)):
    """
    Returns minimal user info for the current token.
    Backend will also try to fetch `profiles` row if present.
    """
    user_id = user["id"]
    # Try to fetch profile (optional)
    resp = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    profile = None
    if isinstance(resp, dict):
        profile = resp.get("data")
        if isinstance(profile, list) and profile:
            profile = profile[0]
    else:
        profile = getattr(resp, "data", None)

    return {"user_id": user_id, "claims": user["claims"], "profile": profile}

@router.post("/create-admin", status_code=201)
async def create_admin(payload: CreateAdminIn, caller=Depends(get_current_admin)):
    """
    Create (or upsert) a profiles row with admin/staff role.
    This endpoint is admin-only. In production consider removing or protecting it
    further (e.g., require an operator JWT).
    """
    # validate role
    role = payload.role.lower()
    if role not in ("admin", "staff", "department_head"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    row = {
        "id": payload.user_id,
        "full_name": payload.full_name,
        "phone": payload.phone,
        "role": role,
        "is_active": True
    }

    # upsert (insert on conflict) using service_key client
    resp = supabase.table("profiles").upsert(row, on_conflict="id").execute()

    # handle client response shapes
    if isinstance(resp, dict):
        if resp.get("error"):
            raise HTTPException(status_code=500, detail=resp["error"])
        return resp.get("data")
    else:
        if getattr(resp, "status_code", 200) not in (200, 201):
            raise HTTPException(status_code=500, detail=getattr(resp, "error_message", "Failed"))
        return getattr(resp, "data", resp)
