"""工具：explain_concept —— 费曼学习法解释概念。"""
from string import Template

from .. import config
from ..agent.llm_client import LLMClient
from ..agent.prompts import get_texts
from .base import BaseTool, ToolResult


class ExplainConceptTool(BaseTool):
    name = "explain_concept"
    description = (
        "用费曼学习法（简单语言+类比+例子）解释一个概念，帮助用户快速理解。"
        "适合用户直接问「什么是XX」或复习中遇到不懂的术语。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "concept": {"type": "string", "description": "要解释的概念名称，如「银行家算法」"}
        },
        "required": ["concept"],
    }

    def __init__(self, llm_client: LLMClient, lang: str | None = None):
        self._llm = llm_client
        self._texts = get_texts(lang or config.AGENT_DEFAULT_LANG)

    async def run(self, concept: str, **kwargs) -> ToolResult:
        user = Template(self._texts["explain_user"]).substitute(concept=concept)
        try:
            data = await self._llm.chat_json(
                [
                    {"role": "system", "content": self._texts["explain_system"]},
                    {"role": "user", "content": user},
                ]
            )
            if not isinstance(data, dict):
                return ToolResult(
                    success=False, error=self._texts["err_not_json_object"]
                )
            return ToolResult(success=True, data=data)
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
