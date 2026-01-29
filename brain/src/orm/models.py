from typing import Optional
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import CommonSqlalchemyMetaMixins


class User(CommonSqlalchemyMetaMixins):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    secrets: Mapped[list["Secret"]] = relationship("Secret", back_populates="user", cascade="all, delete-orphan")


class APIKey(CommonSqlalchemyMetaMixins):
    """API Key model for user authentication."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="api_keys")


class Secret(CommonSqlalchemyMetaMixins):
    """Encrypted secrets storage for users."""

    __tablename__ = "secrets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="secrets")

    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='unique_user_secret_key'),
    )


class Task(CommonSqlalchemyMetaMixins):
    """Task model representing a task in the Jarilo system."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=1)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationship to steps
    steps: Mapped[list["Step"]] = relationship("Step", back_populates="task", cascade="all, delete-orphan")


class Step(CommonSqlalchemyMetaMixins):
    """Step model representing a step within a task."""

    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    step_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    order: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[Optional[str]] = mapped_column(Text)

    # Relationship back to task
    task: Mapped["Task"] = relationship("Task", back_populates="steps")