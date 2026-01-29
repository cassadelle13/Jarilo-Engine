from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from orm.db import get_db_session
from orm.models import APIKey, User

router = APIRouter()


class BootstrapInitRequest(BaseModel):
    name: str = "Admin"
    email: Optional[str] = None
    token: Optional[str] = None


class BootstrapInitResponse(BaseModel):
    user_id: str
    api_key: str


@router.post("/bootstrap/init", response_model=BootstrapInitResponse)
async def bootstrap_init(
    payload: BootstrapInitRequest,
    db: AsyncSession = Depends(get_db_session),
) -> BootstrapInitResponse:
    # If token is configured, require it
    if settings.BOOTSTRAP_TOKEN:
        if not payload.token or payload.token != settings.BOOTSTRAP_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid bootstrap token")

    stmt = select(User).where(User.is_deleted == False).limit(1)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=409, detail="Bootstrap already completed")

    user = User(name=payload.name, email=payload.email)
    db.add(user)
    await db.flush()

    api_key_value = str(uuid.uuid4())
    api_key = APIKey(user_id=user.id, api_key=api_key_value, name="bootstrap")
    db.add(api_key)

    await db.commit()
    await db.refresh(user)

    return BootstrapInitResponse(user_id=user.id, api_key=api_key_value)
