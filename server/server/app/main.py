import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers import assemble, upload, qc, health, mapping, workspace
from .schemas.schemas import Base
from .config.database import engine
from contextlib import asynccontextmanager
from .schemas import schemas
from sqlalchemy import select, delete
from .enums.enums import CeleryStatus
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from fastapi.responses import FileResponse
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # clear all pending jobs and installing databases which have been left hanging from the last server shutdown
        # stmt_delete_pending_queries = delete(schemas.BlastQueries).where(schemas.BlastQueries.status == CeleryStatus.STARTED.value)
        # await conn.execute(stmt_delete_pending_queries)
        
    
    yield
    print("Closing application.. put code on shutdown here")

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(assemble.router)
app.include_router(qc.router)
app.include_router(mapping.router)
app.include_router(health.router)
app.include_router(workspace.router)