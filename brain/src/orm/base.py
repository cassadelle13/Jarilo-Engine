from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_mixin, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models in Jarilo."""


@declarative_mixin
class CommonSqlalchemyMetaMixins(Base):
    __abstract__ = True

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))

    def set_updated_at(self, timestamp: Optional[datetime] = None) -> None:
        """Set the updated_at timestamp."""
        self.updated_at = timestamp or datetime.now(timezone.utc)