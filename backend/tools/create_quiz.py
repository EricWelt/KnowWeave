"""工具：create_quiz —— 根据笔记生成选择题（复用旧 ai-service 的 JSON 防御逻辑）。

答题结果将用于更新 knowledge_states（由 memory 层处理）。
"""
from string import Template

from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..agent.json_utils import parse_json_defensive
from ..agent.llm_client import LLMClient
from ..agent.prompts import get_texts
from ..models import Note
from .base import BaseTool, ToolResult


class CreateQuizTool(BaseTool):
    name = "create_quiz"
    description = (
        "根据指定的笔记内容生成单项选择题（数量可调），用于评估用户掌握程度。"
        "用户作答后 Agent 会更新其知识掌握状态。"
    )
    description_en = (
        "Create multiple-choice questions from the given notes (the count is adjustable) "
        "to check how well the user knows the material. The agent updates the user's "
        "mastery state once they answer."
    )
    parameters = {
        "type": "object",
        "properties": {
            "note_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "出题依据的笔记 ID 列表",
            },
            "count": {"type": "integer", "description": "题目数量，默认 5，最大 10"},
        },
        "required": ["note_ids"],
    }

    def __init__(
        self,
        session: AsyncSession,
        user_id: str,
        llm_client: LLMClient,
        lang: str | None = None,
    ):
        self._session = session
        self._user_id = user_id
        self._llm = llm_client
        self._texts = get_texts(lang or config.AGENT_DEFAULT_LANG)

    async def run(self, note_ids: list[str], count: int = 5, **kwargs) -> ToolResult:
        count = max(1, min(int(count), 10))
        try:
            contents = []
            for nid in note_ids:
                note = await self._session.get(Note, nid)
                if note is not None and note.user_id == self._user_id:
                    contents.append(f"### {note.title}\n{note.content[:3000]}")
            if not contents:
                return ToolResult(
                    success=False, error=self._texts["err_notes_not_found"]
                )

            user = Template(self._texts["quiz_user"]).substitute(
                count=count, contents="\n\n".join(contents)
            )
            text = await self._llm.chat(
                [
                    {"role": "system", "content": self._texts["quiz_system"]},
                    {"role": "user", "content": user},
                ]
            )
            # 防御性解析（旧 ai-service 的 LaTeX 转义修复逻辑）
            data = parse_json_defensive(text)
            if not isinstance(data, list):
                return ToolResult(
                    success=False, error=self._texts["err_quiz_not_array"]
                )
            return ToolResult(success=True, data={"questions": data})
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
