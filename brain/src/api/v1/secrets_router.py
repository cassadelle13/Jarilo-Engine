from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orm.db import get_db_session
from orm.models import Secret, User
from security.auth import get_current_user
from security.encryption import encryption_service

router = APIRouter()


class SecretCreate(BaseModel):
    """Schema for creating a new secret."""
    key: str = Field(..., description="The key name for the secret")
    value: str = Field(..., description="The plaintext value to encrypt and store")


class SecretResponse(BaseModel):
    """Schema for secret response (without revealing the encrypted value)."""
    id: str
    key: str
    created_at: Optional[str]
    updated_at: Optional[str]


class SecretValueResponse(BaseModel):
    """Schema for secret response including decrypted value."""
    id: str
    key: str
    value: str
    created_at: Optional[str]
    updated_at: Optional[str]


@router.post("/secrets", response_model=SecretResponse)
async def create_secret(
    secret_data: SecretCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> SecretResponse:
    """
    Create a new encrypted secret for the current user.

    The secret value is encrypted before storage.
    """
    try:
        # Check if secret with this key already exists for this user
        stmt = select(Secret).where(
            Secret.user_id == current_user.id,
            Secret.key == secret_data.key,
            Secret.is_deleted == False
        )
        result = await db.execute(stmt)
        existing_secret = result.scalar_one_or_none()

        if existing_secret:
            raise HTTPException(status_code=409, detail=f"Secret with key '{secret_data.key}' already exists")

        # Encrypt the value
        encrypted_value = encryption_service.encrypt(secret_data.value)

        # Create new secret
        new_secret = Secret(
            user_id=current_user.id,
            key=secret_data.key,
            encrypted_value=encrypted_value
        )

        db.add(new_secret)
        await db.commit()
        await db.refresh(new_secret)

        return SecretResponse(
            id=new_secret.id,
            key=new_secret.key,
            created_at=new_secret.created_at.isoformat() if new_secret.created_at else None,
            updated_at=new_secret.updated_at.isoformat() if new_secret.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create secret: {str(e)}")


@router.get("/secrets", response_model=List[SecretResponse])
async def list_secrets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> List[SecretResponse]:
    """
    List all secrets for the current user (without values).
    """
    try:
        stmt = select(Secret).where(
            Secret.user_id == current_user.id,
            Secret.is_deleted == False
        ).order_by(Secret.key)

        result = await db.execute(stmt)
        secrets = result.scalars().all()

        return [
            SecretResponse(
                id=secret.id,
                key=secret.key,
                created_at=secret.created_at.isoformat() if secret.created_at else None,
                updated_at=secret.updated_at.isoformat() if secret.updated_at else None
            )
            for secret in secrets
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list secrets: {str(e)}")


@router.get("/secrets/{secret_id}", response_model=SecretValueResponse)
async def get_secret(
    secret_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> SecretValueResponse:
    """
    Get a specific secret with its decrypted value.
    """
    try:
        stmt = select(Secret).where(
            Secret.id == secret_id,
            Secret.user_id == current_user.id,
            Secret.is_deleted == False
        )
        result = await db.execute(stmt)
        secret = result.scalar_one_or_none()

        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")

        # Decrypt the value
        try:
            decrypted_value = encryption_service.decrypt(secret.encrypted_value)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Failed to decrypt secret: {str(e)}")

        return SecretValueResponse(
            id=secret.id,
            key=secret.key,
            value=decrypted_value,
            created_at=secret.created_at.isoformat() if secret.created_at else None,
            updated_at=secret.updated_at.isoformat() if secret.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get secret: {str(e)}")


@router.put("/secrets/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: str,
    secret_data: SecretCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> SecretResponse:
    """
    Update an existing secret's value.
    """
    try:
        stmt = select(Secret).where(
            Secret.id == secret_id,
            Secret.user_id == current_user.id,
            Secret.is_deleted == False
        )
        result = await db.execute(stmt)
        secret = result.scalar_one_or_none()

        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")

        # Check if updating key would conflict with another secret
        if secret_data.key != secret.key:
            stmt = select(Secret).where(
                Secret.user_id == current_user.id,
                Secret.key == secret_data.key,
                Secret.id != secret_id,
                Secret.is_deleted == False
            )
            result = await db.execute(stmt)
            conflicting_secret = result.scalar_one_or_none()
            if conflicting_secret:
                raise HTTPException(status_code=409, detail=f"Secret with key '{secret_data.key}' already exists")

        # Encrypt the new value
        encrypted_value = encryption_service.encrypt(secret_data.value)

        # Update the secret
        secret.key = secret_data.key
        secret.encrypted_value = encrypted_value
        secret.set_updated_at()

        await db.commit()
        await db.refresh(secret)

        return SecretResponse(
            id=secret.id,
            key=secret.key,
            created_at=secret.created_at.isoformat() if secret.created_at else None,
            updated_at=secret.updated_at.isoformat() if secret.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update secret: {str(e)}")


@router.delete("/secrets/{secret_id}")
async def delete_secret(
    secret_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a secret.
    """
    try:
        stmt = select(Secret).where(
            Secret.id == secret_id,
            Secret.user_id == current_user.id,
            Secret.is_deleted == False
        )
        result = await db.execute(stmt)
        secret = result.scalar_one_or_none()

        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")

        # Soft delete
        secret.is_deleted = True
        secret.set_updated_at()

        await db.commit()

        return {"message": "Secret deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete secret: {str(e)}")