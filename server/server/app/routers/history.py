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
from boto3.dynamodb.conditions import Key

router = APIRouter(
    prefix="/api/history",
    tags=['history of commands']
)

# Execute new blast query
@router.get("/{workspace_id}")
async def get_history(
    workspace_id: str,
    session: Session = Depends(get_db),
):
    try:
        response = table.query(
        IndexName="workspace_index",
        KeyConditionExpression=Key("workspace_id").eq(workspace_id)
    )
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Error retrieving history."})
    return response["Items"]
    