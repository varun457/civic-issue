from fastapi import APIRouter, HTTPException
from app.supabase_client import supabase
from supabase.lib.client_options import PostgrestResponse  # optional typing

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/db")
def test_db():
    try:
        res = supabase.table("complaints").select("*").limit(5).execute()

        # ✅ Access data safely
        if not res or not hasattr(res, "data"):
            raise HTTPException(status_code=500, detail="Unexpected Supabase response")

        return {"rows": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
