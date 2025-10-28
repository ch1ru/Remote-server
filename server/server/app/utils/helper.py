import secrets
from ..schemas import schemas
from sqlalchemy import update
from ..enums.enums import CeleryStatus

async def start_celery_job(id: str, cmd: str, session):
    job_id = secrets.token_hex(4) # 4 byte hex string to be a unique job id
    full_job_id = f"{id}_{job_id}"
    new_job = schemas.CeleryJobs(
        id=full_job_id,
        command=cmd,
    )

    async with session.begin():
        session.add(new_job)
        await session.commit()

    return full_job_id

async def update_celery_job_status(id: str, status: CeleryStatus, session):
    async with session.begin():
        await session.execute(
            update(schemas.CeleryJobs)
            .where(schemas.CeleryJobs.id == id)
            .values(status=status.value)
        )
        await session.commit()

    return