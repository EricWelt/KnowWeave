"""工具：explain_concept —— 费曼学习法解释概念。"""
from ..agent.llm_client import LLMClient
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

    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    async def run(self, concept: str, **kwargs) -> ToolResult:
        system = (
            "你是一位擅长费曼学习法的老师。用最通俗的语言解释概念，"
            "必须包含：简单解释、类比、具体例子、相关概念。只输出 JSON 对象，不要额外文字。"
        )
        user = f"请解释概念：{concept}"
        try:
            data = await self._llm.chat_json(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
            )
            if not isinstance(data, dict):
                return ToolResult(success=False, error="LLM 未返回 JSON 对象")
            return ToolResult(success=True, data=data)
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
