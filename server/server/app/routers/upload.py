import hashlib
import uuid
import os
from fastapi import Request, Response, UploadFile, Depends, APIRouter, Form
from typing import Annotated, Union

from fastapi.params import File
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..schemas import schemas
import json
import datetime
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
from celery import uuid

router = APIRouter(
    prefix="/api/upload",
    tags=['File upload']
)

# Fetch all uploaded files
@router.get("/{id}")
async def fetch_uploads(
    id: str,
):
    try:
        files = [f for f in os.listdir(f"/workspace/{id}") if os.path.isfile(os.path.join(f"/workspace/{id}", f))]
        return JSONResponse(status_code=200, content={"files": files})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": "Error fetching uploads."})

# Upload a new fasta file
@router.post("/")
async def upload(
    id: str = Form(...),
    files: List[UploadFile] = File(...),
):
    try:
        #h = hashlib.sha256(id.encode('utf-8')).hexdigest()
        # write to disk
        os.makedirs(f"/workspace/{id}/uploads", exist_ok=True)
        downloaded_files = []
        for file in files:
            os.makedirs(f"/workspace/{id}/uploads/", exist_ok=True)
            file_location = f"/workspace/{id}/uploads/{file.filename}"
            with open(file_location, "wb+") as file_object:
                file_object.write(await file.read())
            downloaded_files.append(file_location)

        # create file path outputs for qc and assembly
        os.makedirs(f"/workspace/{id}/trimmed", exist_ok=True)
        os.makedirs(f"/workspace/{id}/qc", exist_ok=True)
        os.makedirs(f"/workspace/{id}/qc/fastp", exist_ok=True)
        os.makedirs(f"/workspace/{id}/qc/fastqc", exist_ok=True)
        os.makedirs(f"/workspace/{id}/assembly", exist_ok=True)

        return JSONResponse(status_code=200, content={"message": "File uploaded successfully."})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": "Error processing file."})