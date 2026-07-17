"""Agent 会话相关 Pydantic 模型。"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    goal: str


class ChatRequest(BaseModel):
    message: str


class AgentStepOut(BaseModel):
    step: int
    type: str
    summary: str
    tool: str | None = None


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
