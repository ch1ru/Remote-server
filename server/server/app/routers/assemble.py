import secrets
import uuid
import os
from fastapi import Request, Response, UploadFile, Depends, APIRouter, Form, UploadFile, File
from typing import Annotated, Union
from ..utils.helper import start_celery_job
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
from ..config.dynamodb import table
import json

router = APIRouter(
    prefix="/api/assemble",
    tags=['Assembly']
)

# Execute new blast query
@router.post("/")
async def post_assemble(
    id: str = Form(...),
    params: str = Form(...),  # receive as form string
    session: Session = Depends(get_db),
):
    try:
        
        # Validate with pydantic model
        params_dict = spadesParams(**json.loads(params))

        print(params_dict.model_dump())

        full_job_id = await start_celery_job(f"assemble_{id}", "spades", session)

        run_spades.apply_async((params_dict.model_dump(by_alias=True), id), task_id=full_job_id)

        # table.put_item(
        #     Item={
        #         'job_id': full_job_id,
        #         'type': 'assemble',
        #         'created_at': datetime.datetime.utcnow().isoformat(),
        #         'updated_at': datetime.datetime.utcnow().isoformat(),
        #         'params': json.dumps(params_dict.model_dump(by_alias=True)),
        #         'workspace_id': id
        #     }
        # )

        return JSONResponse(status_code=200, content={"message": "Assembly started successfully.", "job_id": full_job_id})
    
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error processing assembly."})
    