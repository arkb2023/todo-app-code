# Pydantic models for todo data
# Defines data schemas, e.g., Todo model with a string text field limited to 140 chars.
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

# SQLAlchemy 2.0+ model
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    __table_args__ = {"schema": "public"}

class TodoDB(Base):
    __tablename__ = "todos"
    
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String(140), nullable=False)
    completed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TodoCreate(BaseModel):
    # Enforces the 140-char limit
    # FastAPI returns `422 Unprocessable Entity`
    text: str = Field(..., max_length=140, min_length=1)

class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    text: str
    completed: bool
    created_at: datetime

class TodoUpdate(BaseModel):
    text: Optional[str] = Field(None, max_length=140, min_length=1)
    completed: Optional[bool] = None

class MessageResponse(BaseModel):
    message: str

# Example usage:
# todo = TodoCreate(text="Buy groceries")
# todo_response = TodoResponse.from_orm(todo_db_instance)