"""Agent 路由：/agent/*。

POST /agent/sessions {goal} → 创建并运行一次完整会话
POST /agent/sessions/{id}/chat {message} → 继续对话
GET  /agent/sessions → 会话列表
GET  /agent/sessions/{id} → 会话详情（含对话历史）
GET  /agent/sessions/{id}/eval → 评测报告

语言：请求体显式字段 lang > Accept-Language 头 > config.AGENT_DEFAULT_LANG。
Prompt、工具描述、步骤摘要与错误信息都按该语言给出。
"""
import json
from collections.abc import Mapping
from string import Template

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..agent.engine import AgentEngine
from ..agent.eval_tracker import EvalTracker
from ..agent.llm_client import LLMClient
from ..agent.memory import MemoryManager
from ..agent.planner import Planner
from ..agent.prompts import get_texts, resolve_lang
from ..core.security import get_current_user
from ..database import get_session
from ..models import AgentSession, EvalLog, User
from ..schemas import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    ChatReply,
    ChatRequest,
    SessionCreateRequest,
    SessionOut,
)
from ..tools import build_registry

router = APIRouter(prefix="/agent", tags=["Agent"])


def _resolve_texts(
    lang: str | None, accept_language: str | None
) -> tuple[str, Mapping[str, str]]:
    """解析本次请求的语言，返回（语言键, 文本表）。"""
    resolved = resolve_lang(lang, accept_language, config.AGENT_DEFAULT_LANG)
    return resolved, get_texts(resolved)


def _build_engine(
    session: AsyncSession,
    user: User,
    lang: str | None = None,
) -> AgentEngine:
    """按请求上下文组装 Agent（依赖注入：session/user/llm/lang）。

    lang 决定进入模型上下文的 Prompt 语言；为空时用 config.AGENT_DEFAULT_LANG。
    """
    llm = LLMClient()
    registry = build_registry(session, user.id, llm, lang)
    tracker = EvalTracker(session, session_id="")
    memory = MemoryManager(session, user.id)
    planner = Planner(llm, lang)
    return AgentEngine(
        session, user.id, registry, llm, tracker, memory, planner, lang
    )


@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(
    request: SessionCreateRequest,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    lang, texts = _resolve_texts(request.lang, accept_language)
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail=texts["err_goal_empty"])
    engine = _build_engine(session, user, lang)
    try:
        result = await engine.start_session(request.goal.strip())
    except Exception as e:  # noqa: BLE001 —— LLM 不可用等外部故障
        raise HTTPException(
            status_code=502,
            detail=Template(texts["err_agent_failed"]).substitute(error=e),
        ) from e
    return result


@router.post("/sessions/{session_id}/chat", response_model=ChatReply)
async def continue_chat(
    session_id: str,
    request: ChatRequest,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    lang, texts = _resolve_texts(request.lang, accept_language)
    engine = _build_engine(session, user, lang)
    try:
        result = await engine.continue_session(session_id, request.message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=Template(texts["err_agent_failed"]).substitute(error=e),
        ) from e
    return {
        "session_id": result["session_id"],
        "reply": result["summary"],
        "conversation": result["conversation"],
    }


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    result = await session.scalars(
        select(AgentSession)
        .where(AgentSession.user_id == user.id)
        .order_by(AgentSession.created_at.desc())
    )
    return [
        {
            "id": s.id,
            "goal": s.goal,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in result.all()
    ]


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    _, texts = _resolve_texts(None, accept_language)
    row = await session.get(AgentSession, session_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail=texts["err_session_missing"])
    try:
        conversation = json.loads(row.conversation_json or "[]")
    except json.JSONDecodeError:
        conversation = []
    return {
        "session_id": row.id,
        "goal": row.goal,
        "status": row.status,
        "conversation": conversation,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/sessions/{session_id}/eval")
async def get_session_eval(
    session_id: str,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    _, texts = _resolve_texts(None, accept_language)
    row = await session.get(AgentSession, session_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail=texts["err_session_missing"])
    result = await session.scalars(
        select(EvalLog).where(EvalLog.session_id == session_id)
    )
    logs = result.all()
    return {
        "session_id": session_id,
        "metrics": {log.metric: log.value for log in logs},
        "details": [json.loads(log.detail_json or "{}") for log in logs],
    }


@router.post("/sessions/{session_id}/answers", response_model=AnswerSubmitResponse)
async def submit_answers(
    session_id: str,
    request: AnswerSubmitRequest,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """提交选择题作答 → 更新知识掌握状态（答题闭环）。"""
    _, texts = _resolve_texts(None, accept_language)
    row = await session.get(AgentSession, session_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail=texts["err_session_missing"])

    total = len(request.answers)
    correct = sum(1 for a in request.answers if a.is_correct)
    # 错误题目的题干作为薄弱点线索
    weak_points = [
        a.question[:30] for a in request.answers if not a.is_correct
    ][:5]

    memory = MemoryManager(session, user.id)
    await memory.update_knowledge(
        topic=row.goal[:12],
        quiz_correct_count=correct,
        quiz_total=total,
        weak_points=weak_points,
    )

    # 取更新后的掌握度
    from ..models import KnowledgeState

    state = await session.scalar(
        select(KnowledgeState).where(
            KnowledgeState.user_id == user.id,
            KnowledgeState.topic == row.goal[:12],
        )
    )
    mastery = state.mastery_level if state is not None else 0.0

    return {
        "session_id": row.id,
        "correct": correct,
        "total": total,
        "mastery_level": round(mastery, 4),
        "weak_points": weak_points,
    }
