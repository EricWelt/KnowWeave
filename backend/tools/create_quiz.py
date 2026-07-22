"""工具：create_quiz —— 根据笔记生成选择题（复用旧 ai-service 的 JSON 防御逻辑）。

答题结果将用于更新 knowledge_states（由 memory 层处理）。
"""
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent.json_utils import parse_json_defensive
from ..agent.llm_client import LLMClient
from ..models import Note
from .base import BaseTool, ToolResult


class CreateQuizTool(BaseTool):
    name = "create_quiz"
    description = (
        "根据指定的笔记内容生成单项选择题（数量可调），用于评估用户掌握程度。"
        "用户作答后 Agent 会更新其知识掌握状态。"
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

    def __init__(self, session: AsyncSession, user_id: str, llm_client: LLMClient):
        self._session = session
        self._user_id = user_id
        self._llm = llm_client

    async def run(self, note_ids: list[str], count: int = 5, **kwargs) -> ToolResult:
        count = max(1, min(int(count), 10))
        try:
            contents = []
            for nid in note_ids:
                note = await self._session.get(Note, nid)
                if note is not None and note.user_id == self._user_id:
                    contents.append(f"### {note.title}\n{note.content[:3000]}")
            if not contents:
                return ToolResult(success=False, error="未找到可用的笔记")

            system = (
                "你是出题机器。必须且只能返回一个合法的 JSON 数组。"
                "如果题目中包含 LaTeX 数学公式，请务必将所有的反斜杠双重转义"
                "（例如写成 \\frac 和 \\|）。"
            )
            joined_contents = "\n\n".join(contents)
            user = f"""根据以下笔记内容，生成 {count} 道单项选择题。
JSON 格式要求必须严格如下：
[
    {{
        "question": "问题内容",
        "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
        "answer": "A. 选项1",
        "explanation": "答案解析"
    }}
]

笔记内容：
{joined_contents}"""

            text = await self._llm.chat(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
            )
            # 防御性解析（旧 ai-service 的 LaTeX 转义修复逻辑）
            data = parse_json_defensive(text)
            if not isinstance(data, list):
                return ToolResult(success=False, error="LLM 未返回题目数组")
            return ToolResult(success=True, data={"questions": data})
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
