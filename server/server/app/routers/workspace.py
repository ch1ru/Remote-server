from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter(
    prefix="/workspace",
    tags=['Quality Control Reads']
)

@router.get("/{full_path:path}")
async def serve_workspace(full_path: str = ""):
    filepath = Path("/workspace") / full_path
    print("filepath")
    print(filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if filepath.is_file():
        return FileResponse(
            filepath,
            filename=filepath.name,
            media_type="application/octet-stream"
        )
    return RedirectResponse(f"/workspace-browse/{full_path}")