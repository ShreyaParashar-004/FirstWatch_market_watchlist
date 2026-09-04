from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "watch"}


@router.get("/api/health")
def api_health():
    return {"status": "ok", "service": "watch"}
