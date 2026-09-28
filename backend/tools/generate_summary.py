"""工具：generate_summary —— 对指定笔记生成摘要/大纲/复习重点。

需要数据库访问（读取笔记内容），故构造时注入 session 与 user_id（依赖注入）。
"""
from string import Template

from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..agent.llm_client import LLMClient
from ..agent.prompts import get_texts
from ..models import Note
from .base import BaseTool, ToolResult


class GenerateSummaryTool(BaseTool):
    name = "generate_summary"
    description = (
        "对指定的一个或多个笔记生成结构化摘要、关键概念列表与建议复习重点。"
        "适合开始复习一个主题时快速建立整体认识。"
    )
    description_en = (
        "Summarize one or more notes into a structured summary, a list of key concepts, "
        "and suggested review points. Useful at the start of revising a topic to build an "
        "overview."
    )
    parameters = {
        "type": "object",
        "properties": {
            "note_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "笔记 ID 列表",
            }
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

    async def run(self, note_ids: list[str], **kwargs) -> ToolResult:
        if not note_ids:
            return ToolResult(success=False, error=self._texts["err_note_ids_empty"])
        try:
            notes = []
            for nid in note_ids:
                note = await self._session.get(Note, nid)
                if note is not None and note.user_id == self._user_id:
                    notes.append(note)
            if not notes:
                return ToolResult(
                    success=False, error=self._texts["err_notes_not_found"]
                )

            contents = "\n\n---\n\n".join(
                f"### {n.title}\n{n.content[:3000]}" for n in notes
            )
            data = await self._llm.chat_json(
                [
                    {"role": "system", "content": self._texts["summary_system"]},
                    {
                        "role": "user",
                        "content": Template(self._texts["summary_user"]).substitute(
                            contents=contents
                        ),
                    },
                ]
            )
            return ToolResult(success=True, data=data)
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
