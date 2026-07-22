"""工具：generate_summary —— 对指定笔记生成摘要/大纲/复习重点。

需要数据库访问（读取笔记内容），故构造时注入 session 与 user_id（依赖注入）。
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent.llm_client import LLMClient
from ..models import Note
from .base import BaseTool, ToolResult


class GenerateSummaryTool(BaseTool):
    name = "generate_summary"
    description = (
        "对指定的一个或多个笔记生成结构化摘要、关键概念列表与建议复习重点。"
        "适合开始复习一个主题时快速建立整体认识。"
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

    def __init__(self, session: AsyncSession, user_id: str, llm_client: LLMClient):
        self._session = session
        self._user_id = user_id
        self._llm = llm_client

    async def run(self, note_ids: list[str], **kwargs) -> ToolResult:
        if not note_ids:
            return ToolResult(success=False, error="note_ids 不能为空")
        try:
            notes = []
            for nid in note_ids:
                note = await self._session.get(Note, nid)
                if note is not None and note.user_id == self._user_id:
                    notes.append(note)
            if not notes:
                return ToolResult(success=False, error="未找到可用的笔记")

            contents = "\n\n---\n\n".join(
                f"### {n.title}\n{n.content[:3000]}" for n in notes
            )
            system = (
                "你是学习助手。根据笔记内容输出 JSON 对象："
                '{"summary": "markdown 格式结构化摘要", "key_concepts": ["概念1",...], '
                '"suggested_review_focus": ["需要重点复习的内容"]}。只输出 JSON。'
            )
            data = await self._llm.chat_json(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"笔记内容：\n{contents}"},
                ]
            )
            return ToolResult(success=True, data=data)
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
