import uuid
import os
from fastapi import Request, Response, UploadFile, Depends, APIRouter, Form
from typing import Annotated, Union
from ..utils.helper import start_celery_job
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..schemas import schemas
from ..models.params import multiqcParams, fastpParams, fastqcParams
from ..enums.enums import CeleryStatus
import json
from typing import Literal
import datetime
from fastapi.responses import HTMLResponse, JSONResponse
from ..worker.worker import run_fastp, run_fastqc
from celery.result import AsyncResult
from celery import uuid

router = APIRouter(
    prefix="/api/qc",
    tags=['Quality Control Reads']
)

# Execute new blast query
@router.post("/fastp")
async def post_fastp(
    id: str = Form(...),
    params: str = Form(...),  # receive as form string
    session: Session = Depends(get_db),
):
    try:
        # Validate with pydantic model
        params_dict = fastpParams(**json.loads(params))

        full_job_id = await start_celery_job(f"assemble_{id}", "fastp", session)

        run_fastp.apply_async((params_dict.model_dump(), id), task_id=full_job_id)

        return JSONResponse(status_code=200, content={"message": "Assembly started successfully.", "job_id": full_job_id})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error processing fastp."})

# Execute new blast query
@router.post("/fastqc")
async def post_fastqc(
    id: str = Form(...),
    params: str = Form(...),  # receive as form string
    session: Session = Depends(get_db),
):
    try:
        # Validate with pydantic model
        params_dict = fastqcParams(**json.loads(params))

        full_job_id = await start_celery_job(f"assemble_{id}", "fastqc", session)

        run_fastqc.apply_async((params_dict.model_dump(), id), task_id=full_job_id)

        return JSONResponse(status_code=200, content={"message": "Fastqc started successfully.", "job_id": full_job_id})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error processing fastqc."})


@router.get("/fastp")
async def get_fastp(
    request: Request
):
    
    try:
        html_report = ""
        extension: Literal["json", "html"] = request.query_params.get("ext_type")
        id = request.query_params.get("id")

        with open(f"/workspace/{id}/qc/fastp/fastp_report.{extension}", "r") as f:
            html_report = f.read()

        return HTMLResponse(content=html_report, status_code=200)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error fetching fastp report."})
    
@router.get("/fastqc")
async def get_fastqc(
    request: Request
):
    
    try:
        html_report = ""
        id = request.query_params.get("id")
        filename = request.query_params.get("filename")

        with open(f"/workspace/{id}/qc/fastqc/{filename}_fastqc.html", "r") as f:
            html_report = f.read()

        return HTMLResponse(content=html_report, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error fetching fastp report."})

