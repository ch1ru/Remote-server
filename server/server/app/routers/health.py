from fastapi import APIRouter

router = APIRouter(
    prefix="/api/health",
    tags=['Health check']
)

# Execute new blast query
@router.get("/")
async def post_assembly():
    return {"message": "Assembly endpoint is operational."}