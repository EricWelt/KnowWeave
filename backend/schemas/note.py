"""笔记相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="")


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None


class NoteOut(BaseModel):
    id: str
    title: str
    content: str
    source_type: str
    source_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
