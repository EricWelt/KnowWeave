"""笔记 ↔ 向量库 同步器。

职责：
- index_note: 笔记内容 → 分块 → embedding → ChromaDB 入库 → 写 note_chunks 映射
- remove_from_index: 删除 ChromaDB 分块 + note_chunks 记录

被 notes/upload 路由调用；测试中可 monkeypatch（避免真实模型加载）。
"""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Note, NoteChunk
from . import embedder, vector_store
from .chunker import split_text


async def index_note(
    note: Note, session: AsyncSession | None = None
) -> list[str]:
    """索引一篇笔记（先清旧块再入库）。返回 chroma_id 列表。"""
    # 1) 清掉旧的（幂等，防止重复索引）
    await remove_from_index(note.id, session)

    # 2) 分块
    chunks = split_text(note.content)
    if not chunks:
        return []

    # 3) 向量化 + 入库
    embeddings = embedder.embed_texts(chunks)
    chroma_ids = vector_store.add_chunks(
        note_id=note.id,
        note_title=note.title,
        chunks=chunks,
        embeddings=embeddings,
        source_type=note.source_type,
    )

    # 4) 写 note_chunks 映射表
    if session is not None:
        for i, (chunk, cid) in enumerate(zip(chunks, chroma_ids)):
            session.add(
                NoteChunk(
                    note_id=note.id,
                    chunk_index=i,
                    chroma_id=cid,
                    content_preview=chunk[:100],
                )
            )
        await session.commit()
    return chroma_ids


async def remove_from_index(
    note_id: str, session: AsyncSession | None = None
) -> None:
    """清理笔记在 ChromaDB 与 note_chunks 中的全部痕迹。"""
    vector_store.delete_by_note(note_id)
    if session is not None:
        await session.execute(
            delete(NoteChunk).where(NoteChunk.note_id == note_id)
        )
        await session.commit()


async def get_note_chunk_count(
    note_id: str, session: AsyncSession
) -> int:
    result = await session.scalar(
        select(NoteChunk).where(NoteChunk.note_id == note_id)
    )
    return result.count() if result is not None else 0
