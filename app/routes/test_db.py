from fastapi import APIRouter
from app.supabase_client import supabase

router = APIRouter()

@router.get("/test-db")
def test_db():
    try:
        data = supabase.table("complaints").select("*").limit(5).execute()
        return {"rows": data.data}
    except Exception as e:
        return {"error": str(e)}
