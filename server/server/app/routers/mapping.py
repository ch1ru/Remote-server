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
from ..models.params import bwaMemParams, bwaIndexParams
from ..enums.enums import CeleryStatus
import json
import datetime
from fastapi.responses import JSONResponse, StreamingResponse
from ..worker.worker import run_bwa_mem, run_bwa_index, run_convert_to_bam
from celery.result import AsyncResult
from celery import uuid
from ..config.dynamodb import table

router = APIRouter(
    prefix="/api/mapping",
    tags=['Map reads to reference genome']
)

# Bwa
@router.post("/bwa/mem")
async def post_bwa_mem(
    id: str = Form(...),
    params: str = Form(...),  # receive as form string
    filenames: List[str] = Form(...),
    out: str = Form(...),
    session: Session = Depends(get_db),
):
    try:

        # TODO: add params processing if needed

        full_job_id = await start_celery_job(f"assemble_{id}", "bwa mem", session)

        run_bwa_mem.apply_async((filenames, id, out), task_id=full_job_id)

        # table.put_item(
        #     Item={
        #         'job_id': full_job_id,
        #         'type': 'mapping',
        #         'created_at': datetime.datetime.utcnow().isoformat(),
        #         'updated_at': datetime.datetime.utcnow().isoformat(),
        #         'params': params,
        #         'workspace_id': id
        #     }
        # )

        return JSONResponse(status_code=200, content={"message": "BWA mem started successfully.", "job_id": full_job_id})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error processing Bwa mem."})

# Index a reference genome
@router.post("/bwa/index")
async def post_bwa_index(
    id: str = Form(...),
    params: str = Form(...),  # receive as form string
    filenames: List[str] = Form(...),
    session: Session = Depends(get_db),
):
    try:

        # TODO: add params processing if needed

        full_job_id = await start_celery_job(f"assemble_{id}", "bwa index", session)

        run_bwa_index.apply_async((filenames, id), task_id=full_job_id)

        # table.put_item(
        #     Item={
        #         'job_id': full_job_id,
        #         'type': 'mapping',
        #         'created_at': datetime.datetime.utcnow().isoformat(),
        #         'updated_at': datetime.datetime.utcnow().isoformat(),
        #         'params': params,
        #         'workspace_id': id
        #     }
        # )

        return JSONResponse(status_code=200, content={"message": "Indexing started successfully.", "job_id": full_job_id})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error processing Indexing."})
    
@router.post("/samtools")
async def post_samtools(
    id: str = Form(...),
    bam_file: str = Form(...),
    sam_file: str = Form(...),
    session: Session = Depends(get_db),
):
    try:

        full_job_id = await start_celery_job(f"assemble_{id}", "samtools", session)

        run_convert_to_bam.apply_async((sam_file, bam_file, id), task_id=full_job_id)

        # table.put_item(
        #     Item={
        #         'job_id': full_job_id,
        #         'type': 'samtools',
        #         'created_at': datetime.datetime.utcnow().isoformat(),
        #         'updated_at': datetime.datetime.utcnow().isoformat(),
        #         'params': json.dumps({}),
        #         'workspace_id': id
        #     }
        # )

        return JSONResponse(status_code=200, content={"message": "Conversion to BAM started successfully.", "job_id": full_job_id})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error processing conversion to BAM."})
    
@router.get("/bam")
async def download_bam(
    request: Request,
):
    try:
        id = request.query_params.get("id")
        file = request.query_params.get("file")
        bam_path = f"/workspace/{id}/mapping/{file}.sorted.dedup.q20.bam"

        def iterfile():
            with open(bam_path, mode="rb") as f:
                for chunk in iter(lambda: f.read(1024*1024), b""):
                    yield chunk

        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file}.sorted.dedup.q20.bam"}
        )

        
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error fetching BAM status."})