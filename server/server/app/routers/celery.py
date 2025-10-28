import secrets
import uuid
import os
from fastapi import Request, Response, UploadFile, Depends, APIRouter, Form, UploadFile, File
from typing import Annotated, Union
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..schemas import schemas
from ..models.params import spadesParams
from ..enums.enums import CeleryStatus
import json
import datetime
from fastapi.responses import JSONResponse
from ..worker.worker import run_spades
from celery.result import AsyncResult
from celery import uuid

router = APIRouter(
    prefix="/api/celery",
    tags=['Celery jobs']
)

# Execute new blast query
@router.get("/")
async def fetch_assembly(
    id: str,
    session: Session = Depends(get_db),
):
    job = await session.execute(select(schemas.CeleryJobs).where(schemas.CeleryJobs.id == id))
    job_data = job.scalar()

    return job_data