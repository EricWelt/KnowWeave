"""工具集：registry 构建入口。"""
from ..agent.llm_client import LLMClient
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseTool, ToolRegistry, ToolResult
from .create_quiz import CreateQuizTool
from .cross_reference import CrossReferenceTool
from .explain_concept import ExplainConceptTool
from .generate_summary import GenerateSummaryTool
from .search_notes import SearchNotesTool

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "ToolResult",
    "SearchNotesTool",
    "GenerateSummaryTool",
    "CreateQuizTool",
    "CrossReferenceTool",
    "ExplainConceptTool",
]


def build_registry(session: AsyncSession, user_id: str, llm: LLMClient) -> ToolRegistry:
    """按请求上下文构建工具注册表（依赖注入：session/user/llm）。"""
    registry = ToolRegistry()
    registry.register(SearchNotesTool())
    registry.register(GenerateSummaryTool(session, user_id, llm))
    registry.register(CreateQuizTool(session, user_id, llm))
    registry.register(CrossReferenceTool(session, user_id, llm))
    registry.register(ExplainConceptTool(llm))
    return registry
