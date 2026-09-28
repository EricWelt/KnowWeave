"""Agent 会话相关 Pydantic 模型。"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    goal: str
    # 可选的 BCP 47 语言标签（如 "zh-Hans" / "en"）：优先于 Accept-Language
    lang: str | None = None


class ChatRequest(BaseModel):
    message: str
    lang: str | None = None


class AgentStepOut(BaseModel):
    step: int
    type: str
    summary: str
    tool: str | None = None
    # 显式成败标记：界面据此判断工具是否失败，不必从 summary 文本里猜
    success: bool = True
    error: str | None = None


class EvalSummary(BaseModel):
    task_completion_rate: float | None = None
    tool_call_success_rate: float | None = None
    avg_latency_ms: float | None = None
    plan_deviation_rate: float | None = None


class SessionOut(BaseModel):
    session_id: str
    summary: str
    plan: list[Any] = []
    steps: list[AgentStepOut] = []
    eval: EvalSummary | None = None
    weak_points: list[str] = []
    conversation: list[dict[str, Any]] = []


class ChatReply(BaseModel):
    session_id: str
    reply: str
    conversation: list[dict[str, Any]] = []

class QuizAnswerItem(BaseModel):
    """用户的一道作答记录。"""
    question: str
    selected: str
    correct: str
    is_correct: bool


class AnswerSubmitRequest(BaseModel):
    """提交一次作答结果。"""
    answers: list[QuizAnswerItem]


class AnswerSubmitResponse(BaseModel):
    session_id: str
    correct: int
    total: int
    mastery_level: float
    weak_points: list[str]
