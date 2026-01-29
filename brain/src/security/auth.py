import uuid
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orm.db import get_db_session
from orm.models import APIKey, User

security = HTTPBearer()


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Dependency to get the current authenticated user from Bearer token.

    Args:
        auth: HTTP Authorization credentials containing the API key
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        api_key_value = auth.credentials

        # First try to find API key
        stmt = select(APIKey).where(APIKey.api_key == api_key_value, APIKey.is_deleted == False)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if api_key:
            # Load the user
            stmt = select(User).where(User.id == api_key.user_id, User.is_deleted == False)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user

        # If not found, raise authentication error
        raise HTTPException(status_code=401, detail="Invalid API key")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


async def get_current_user_id(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> str:
    """
    Dependency to get the current authenticated user ID from Bearer token.

    Args:
        auth: HTTP Authorization credentials containing the API key
        db: Database session

    Returns:
        str: The authenticated user ID

    Raises:
        HTTPException: If authentication fails
    """
    user = await get_current_user(auth, db)
    return user.id


async def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Optional dependency to get the current user if authenticated.

    Returns None if no authentication provided or invalid.
    """
    if not auth:
        return None

    try:
        return await get_current_user(auth, db)
    except HTTPException:
        return None