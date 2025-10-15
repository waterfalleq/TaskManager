from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from datetime import datetime, timezone

from app.db.database import Base
from .enums import TaskStatus, TaskPriority


def utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """Database model for application users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Task(Base):
    """Database model for user tasks."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.NONE)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
