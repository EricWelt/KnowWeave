"""knowledge_states 表：长期记忆核心（知识掌握状态）。

UNIQUE(user_id, topic) 确保每个用户对每个主题只有一条记录；
mastery_level 0.0-1.0，随复习与答题正确率动态更新。
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class KnowledgeState(Base):
    __tablename__ = "knowledge_states"
    __table_args__ = (UniqueConstraint("user_id", "topic", name="uq_user_topic"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    quiz_correct_rate: Mapped[float] = mapped_column(Float, default=0.0)
    weak_points_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
