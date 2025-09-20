from fastapi import APIRouter, File, UploadFile, HTTPException
from ..supabase_client import supabase
import uuid

router = APIRouter(prefix="/test", tags=["test"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split('.')[-1]
        unique_name = f"{uuid.uuid4()}.{file_ext}"

        content = await file.read()

        # ✅ Upload to Supabase Storage
        res = supabase.storage.from_("complaint-images").upload(unique_name, content)

        # ✅ Do NOT call res.get(...) or res.error – just inspect as dict
        if isinstance(res, dict) and "error" in res:
            raise HTTPException(status_code=400, detail=res["error"]["message"])

        # ✅ Build a public URL
        public_url = supabase.storage.from_("complaint-images").get_public_url(unique_name)
        return {"file_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
