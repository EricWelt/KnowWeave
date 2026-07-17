"""笔记路由：/notes CRUD + reindex，含 RAG 同步。

创建 → 分块入库；更新 → 重建索引；删除 → 清理向量；reindex → 手动重建。
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import get_current_user
from ..database import get_session
from ..models import Note, User
from ..rag.indexer import index_note, remove_from_index
from ..schemas import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["笔记"])


async def _get_owned_note(
    note_id: str, user: User, session: AsyncSession
) -> Note:
    note = await session.get(Note, note_id)
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


@router.get("", response_model=list[NoteOut])
async def list_notes(
    search: str | None = Query(default=None, description="按标题模糊搜索"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Note]:
    stmt = select(Note).where(Note.user_id == user.id)
    if search:
        stmt = stmt.where(Note.title.contains(search))
    stmt = stmt.order_by(Note.updated_at.desc())
    result = await session.scalars(stmt)
    return list(result.all())


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    request: NoteCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    note = Note(
        user_id=user.id,
        title=request.title,
        content=request.content,
        source_type="manual",
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    try:
        await index_note(note, session)
    except Exception as e:
        print(f"[notes] 索引失败 note={note.id}: {e}")
    return note


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    return await _get_owned_note(note_id, user, session)


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: str,
    request: NoteUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    note = await _get_owned_note(note_id, user, session)
    if request.title is not None:
        note.title = request.title
    if request.content is not None:
        note.content = request.content
    await session.commit()
    await session.refresh(note)
    try:
        await index_note(note, session)
    except Exception as e:
        print(f"[notes] 重建索引失败 note={note.id}: {e}")
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    note = await _get_owned_note(note_id, user, session)
    try:
        await remove_from_index(note.id, session)
    except Exception as e:
        print(f"[notes] 清理索引失败 note={note.id}: {e}")
    await session.delete(note)
    await session.commit()


@router.post("/{note_id}/reindex", response_model=NoteOut)
async def reindex_note(
    note_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    """手动触发重新索引（如上传时索引失败后的重试）。"""
    note = await _get_owned_note(note_id, user, session)
    await index_note(note, session)
    await session.refresh(note)
    return note
