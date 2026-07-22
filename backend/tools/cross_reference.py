"""工具：cross_reference —— 跨笔记关联（知识图谱）。

流程：向量检索相似分块 → 按笔记聚合命中数 → 取 top-3 笔记 → LLM 生成关联原因。
"""
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent.llm_client import LLMClient
from ..models import Note
from ..rag import embedder, vector_store
from .base import BaseTool, ToolResult


class CrossReferenceTool(BaseTool):
    name = "cross_reference"
    description = (
        "找出与指定笔记内容相关的其他笔记（跨笔记知识关联），返回关联笔记及其原因。"
        "适合发现知识间的联系、建立知识网络。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "note_id": {"type": "string", "description": "源笔记 ID"}
        },
        "required": ["note_id"],
    }

    def __init__(self, session: AsyncSession, user_id: str, llm_client: LLMClient):
        self._session = session
        self._user_id = user_id
        self._llm = llm_client

    async def run(self, note_id: str, **kwargs) -> ToolResult:
        try:
            note = await self._session.get(Note, note_id)
            if note is None or note.user_id != self._user_id:
                return ToolResult(success=False, error="笔记不存在")

            # 1) 用笔记前几段做多次检索，聚合命中
            hits_by_note: dict[str, int] = {}
            for chunk in note.content[:6000].split("\n\n")[:5]:
                if not chunk.strip():
                    continue
                emb = embedder.embed_query(chunk[:200])
                for r in vector_store.query_chunks(emb, n_results=5):
                    if r["note_id"] != note_id:
                        hits_by_note[r["note_id"]] = (
                            hits_by_note.get(r["note_id"], 0) + 1
                        )

            # 2) 取命中数最多的 3 篇
            top_ids = sorted(hits_by_note, key=hits_by_note.get, reverse=True)[:3]
            related = []
            for nid in top_ids:
                n = await self._session.get(Note, nid)
                if n is not None:
                    related.append({"note_id": n.id, "title": n.title})

            # 3) LLM 为每篇生成一句关联原因
            if related:
                system = "你是知识图谱助手。为每对笔记生成一句关联原因，输出 JSON 数组。"
                user = (
                    f"源笔记《{note.title}》与以下笔记相关：\n"
                    + "\n".join(f"- {r['title']}" for r in related)
                    + "\n输出 [{\"title\": ..., \"reason\": \"...\"}]"
                )
                try:
                    reasons = await self._llm.chat_json(
                        [{"role": "system", "content": system}, {"role": "user", "content": user}]
                    )
                    reason_map = {
                        r.get("title", ""): r.get("reason", "") for r in reasons
                    } if isinstance(reasons, list) else {}
                except Exception:  # noqa: BLE001 —— 原因生成失败不阻断关联
                    reason_map = {}

            results = [
                {
                    "note_id": r["note_id"],
                    "title": r["title"],
                    "relevance": "高",
                    "reason": reason_map.get(r["title"], ""),
                }
                for r in related
            ]
            return ToolResult(success=True, data={"related_notes": results})
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=str(e))
