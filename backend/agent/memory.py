"""三层记忆管理器。

短期记忆：会话对话历史（agent_sessions.conversation_json），取最近 N 轮入 context；
长期记忆：knowledge_states 表 —— 会话结束后更新 mastery_level / 薄弱点 / 复习次数；
语义记忆：ChromaDB 笔记分块（经 search_notes 工具访问，不在此层）。

mastery 更新公式（可解释、可调）：
- 有答题：mastery = 0.3*旧值 + 0.7*本次正确率（EMA 式加权）
- 无答题：mastery = min(1, 旧值 + 0.05)（复习即小幅提升）
- quiz_correct_rate = 正确题数 / 总题数
- weak_points 由本次答题的错误题对应知识点合并去重
"""
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..models import AgentSession, KnowledgeState

_MASTERY_WEIGHT_OLD = 0.3
_MASTERY_WEIGHT_NEW = 0.7
_REVIEW_BUMP = 0.05


class MemoryManager:
    def __init__(self, session: AsyncSession, user_id: str):
        self._session = session
        self._user_id = user_id

    # ---------- 读 ----------

    async def load_knowledge_summary(self) -> str:
        """把用户全部知识状态压缩成一行行摘要，注入 system_prompt。"""
        result = await self._session.scalars(
            select(KnowledgeState).where(
                KnowledgeState.user_id == self._user_id
            )
        )
        states = list(result.all())
        if not states:
            return ""
        lines = []
        for s in states:
            weak = "、".join(json.loads(s.weak_points_json or "[]"))
            lines.append(
                f"- {s.topic}: 掌握度{s.mastery_level:.2f}, 复习{s.review_count}次, "
                f"正确率{s.quiz_correct_rate:.0%}"
                + (f", 薄弱点: {weak}" if weak else "")
            )
        return "\n".join(lines)

    async def load_recent_conversation(
        self, session_id: str, max_turns: int | None = None
    ) -> list[dict]:
        """读取会话历史，返回最近 max_turns 轮（默认 config.MEMORY_RECENT_TURNS）。"""
        session_row = await self._session.get(AgentSession, session_id)
        if session_row is None:
            return []
        try:
            history = json.loads(session_row.conversation_json or "[]")
        except json.JSONDecodeError:
            return []
        max_turns = max_turns or config.MEMORY_RECENT_TURNS
        return history[-max_turns:]

    # ---------- 写 ----------

    async def save_conversation(
        self, session_id: str, conversation: list[dict]
    ) -> None:
        session_row = await self._session.get(AgentSession, session_id)
        if session_row is not None:
            session_row.conversation_json = json.dumps(
                conversation, ensure_ascii=False
            )
            await self._session.commit()

    async def update_knowledge(
        self,
        topic: str,
        quiz_correct_count: int,
        quiz_total: int,
        weak_points: list[str],
    ) -> None:
        """会话结束后更新（或创建）一个主题的知识状态。"""
        if not topic:
            return
        stmt = select(KnowledgeState).where(
            KnowledgeState.user_id == self._user_id,
            KnowledgeState.topic == topic,
        )
        state = await self._session.scalar(stmt)
        if state is None:
            state = KnowledgeState(
                user_id=self._user_id, topic=topic, review_count=0
            )
            self._session.add(state)

        correct_rate = quiz_correct_count / quiz_total if quiz_total > 0 else 0.0
        # 新记录 flush 前 mastery_level/quiz_correct_rate 为 None（列默认值在插入时才生效）
        old_mastery = state.mastery_level or 0.0
        if quiz_total > 0:
            state.mastery_level = min(
                1.0,
                _MASTERY_WEIGHT_OLD * old_mastery
                + _MASTERY_WEIGHT_NEW * correct_rate,
            )
            state.quiz_correct_rate = correct_rate
        else:
            state.mastery_level = min(1.0, old_mastery + _REVIEW_BUMP)

        state.review_count += 1
        state.last_reviewed = datetime.now(timezone.utc).replace(tzinfo=None)  # SQLite naive UTC

        # 合并薄弱点（去重、保留既有 + 新增）
        existing = json.loads(state.weak_points_json or "[]")
        merged = list(dict.fromkeys(existing + weak_points))
        state.weak_points_json = json.dumps(merged, ensure_ascii=False)

        await self._session.commit()
