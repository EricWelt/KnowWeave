"""工具：search_notes —— 向量检索笔记分块（async run）。

设计说明：FastAPI 全异步栈，工具 run() 为 async 以便内部 await LLM/数据库调用。
"""
from ..rag import embedder, vector_store
from .base import BaseTool, ToolResult


class SearchNotesTool(BaseTool):
    name = "search_notes"
    description = (
        "根据用户查询在笔记库中做语义检索，返回最相关的笔记片段（含所属笔记、"
        "分块内容与相关度分数）。用于复习时回忆知识点、定位知识点所在的笔记。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "检索查询，如「进程调度算法」"}
        },
        "required": ["query"],
    }

    async def run(self, query: str, **kwargs) -> ToolResult:
        try:
            query_embedding = embedder.embed_query(query)
            results = vector_store.query_chunks(query_embedding, n_results=5)
            return ToolResult(success=True, data={"results": results})
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
