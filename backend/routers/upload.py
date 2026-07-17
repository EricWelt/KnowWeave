"""文件上传路由：/upload。

流程：校验类型 → 保存临时 → 解析 → 建笔记 → 分块入库 → 清理临时文件。
"""
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..core.security import get_current_user
from ..database import get_session
from ..ingestion import parse_file
from ..models import Note, User
from ..rag.indexer import index_note

router = APIRouter(prefix="/upload", tags=["文件上传"])


@router.post("", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext or '(无扩展名)'}，仅支持 pdf/pptx/md",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")

    # 解析（失败 → 友好错误）
    try:
        text, title = parse_file(ext, content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="未能从文件中提取到文字（可能是扫描版 PDF），暂不支持",
        )

    # 扩展名 → source_type 取值
    source_type = {".pdf": "pdf", ".pptx": "pptx", ".md": "markdown"}[ext]
    note = Note(
        user_id=user.id,
        title=title[:200],
        content=text,
        source_type=source_type,
        source_name=file.filename,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    # 分块 → embedding → ChromaDB（失败不阻断笔记创建，但记录日志）
    try:
        await index_note(note, session)
    except Exception as e:
        # 索引失败不影响已保存的笔记；重试可调用 /notes/{id}/reindex
        print(f"[upload] 索引失败 note={note.id}: {e}")

    return {"note_id": note.id, "title": note.title}
