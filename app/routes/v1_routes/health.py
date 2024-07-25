from fastapi import APIRouter


router = APIRouter()
endpoint_name = "health_check"


@router.get("/health")
async def get_health():
    return {"status": "ok"}
