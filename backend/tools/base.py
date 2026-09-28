"""工具基类 + 注册中心。

设计要点：
- parameters 用 JSON Schema —— 与 OpenAI function calling 格式一致，可直接拼 Prompt；
- description 是 LLM 决定「何时调用」的唯一依据，必须写清功能和适用场景；
- ToolRegistry 提供 register/get/all/specs，engine 启动时遍历注册表生成工具描述。
"""
from dataclasses import dataclass
from typing import Any

from ..agent.prompts import EN_LANG


@dataclass
class ToolResult:
    """统一工具返回：success + data/error 二选一。"""
    success: bool
    data: Any = None
    error: str | None = None


class BaseTool:
    """所有工具的基类。子类实现 run()。"""

    name: str = ""
    description: str = ""  # 中文描述（默认）
    description_en: str = ""  # 英文描述；为空时回落 description
    parameters: dict = {}  # JSON Schema

    def localized_description(self, lang: str) -> str:
        """按语言取工具描述。英文缺失时回落中文——宁可让模型读到中文，也不给空描述。"""
        if lang == EN_LANG and self.description_en:
            return self.description_en
        return self.description

    def run(self, **kwargs) -> ToolResult:
        raise NotImplementedError

    def to_spec(self) -> dict:
        """序列化为 OpenAI function-calling 格式（供注入 Prompt）。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """{tool.name: tool} 字典 + 注册/查询/描述生成。"""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError("工具必须定义 name")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def specs(self) -> list[dict]:
        return [t.to_spec() for t in self.all()]

    def descriptions(self, lang: str) -> str:
        """生成注入 system prompt 的纯文本工具清单（描述按语言取）。

        工具描述是模型判断「该不该调这个工具」的唯一依据，因此必须随语言切换；
        工具名与参数名保持英文标识，它们是代码常量。
        """
        lines = []
        for t in self.all():
            props = t.parameters.get("properties", {})
            params = ", ".join(f"{k}({v.get('type','?')})" for k, v in props.items())
            lines.append(
                f"- {t.name}({params}): {t.localized_description(lang)}"
            )
        return "\n".join(lines)
