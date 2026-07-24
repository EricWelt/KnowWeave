"""Agent 引擎测试：用 FakeLLMClient 脚本化控制 LLM 行为。

这是「如何测试 Agent」的核心教学样例：
- LLM 是不可控外部依赖 → 用脚本化假客户端注入，精确驱动每条分支；
- 验证：循环终止、工具调度、异常恢复、JSON 容错、记忆更新、评测落库。
"""
import json

import pytest
from sqlalchemy import select

from backend import config
from backend.agent.eval_tracker import EvalTracker
from backend.agent.engine import AgentEngine
from backend.agent.json_utils import parse_json_defensive
from backend.agent.llm_client import LLMClient
from backend.agent.memory import MemoryManager
from backend.agent.planner import Planner
from backend.models import AgentSession, EvalLog, KnowledgeState, User
from backend.tools.base import BaseTool, ToolResult


# ==================== 测试替身 ====================

class FakeLLMClient(LLMClient):
    """按脚本顺序返回预设响应；脚本元素可以是字符串或 callable(messages)->str。"""

    def __init__(self, script: list):
        self.script = list(script)
        self.calls: list[list[dict]] = []

    async def chat(self, messages, **kwargs):
        self.calls.append(messages)
        if self.script:
            resp = self.script.pop(0)
            if callable(resp):
                resp = resp(messages)
            return resp
        return '{"thought": "默认结束", "action": "final", "params": {"answer": "默认答案"}}'

    async def chat_json(self, messages, **kwargs):
        return parse_json_defensive(await self.chat(messages, **kwargs))


class FakeEchoTool(BaseTool):
    name = "echo"
    description = "回显工具"
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    async def run(self, text: str, **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"echo": text})


class FakeFailTool(BaseTool):
    name = "boom"
    description = "总是失败的工具"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    async def run(self, **kwargs) -> ToolResult:
        return ToolResult(success=False, error="模拟失败")


def _plan_json(n=3):
    return json.dumps(
        [{"step": i, "action": f"步骤{i}", "tool": "echo" if i == 1 else None} for i in range(1, n + 1)]
    )


def _think(action: str, **params):
    return json.dumps({"thought": "思考", "action": action, "params": params})


async def _make_engine(db_session, llm, registry=None):
    from backend.tools import ToolRegistry

    user = User(username=f"u{id(llm)}", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    if registry is None:
        registry = ToolRegistry()
        registry.register(FakeEchoTool())
        registry.register(FakeFailTool())

    tracker = EvalTracker(db_session, session_id="")
    memory = MemoryManager(db_session, user.id)
    planner = Planner(llm)
    return AgentEngine(db_session, user.id, registry, llm, tracker, memory, planner)


# ==================== 用例 ====================

async def test_single_final_answer(db_session):
    llm = FakeLLMClient(script=[_plan_json(), _think("final", answer="直接回答完毕")])
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("复习操作系统")
    assert result["summary"] == "直接回答完毕"
    assert result["eval"]["tool_call_success_rate"] == 0.0  # 没调工具
    # 会话已落库
    row = await db_session.get(AgentSession, result["session_id"])
    assert row is not None
    assert row.status == "completed"
    assert "直接回答完毕" in row.conversation_json


async def test_tool_call_then_final(db_session):
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            _think("echo", text="你好"),
            _think("final", answer="完成，已回显"),
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("复习")
    assert result["summary"] == "完成，已回显"
    # 应该有 act 步骤且成功
    acts = [s for s in result["steps"] if s["type"] == "act"]
    assert len(acts) == 1
    assert acts[0]["tool"] == "echo"
    assert result["eval"]["tool_call_success_rate"] == 1.0
    # 工具观察进入了对话
    obs = [m for m in result["conversation"] if "echo" in m.get("content", "")]
    assert obs, "工具返回应出现在对话中"


async def test_tool_failure_does_not_crash(db_session):
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            _think("boom"),
            _think("final", answer="工具失败了但我继续了"),
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("测试容错")
    assert "工具失败了但我继续了" == result["summary"]
    assert result["eval"]["tool_call_success_rate"] == 0.0  # boom 失败


async def test_unknown_tool_recovers(db_session):
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            _think("no_such_tool"),
            _think("final", answer="识别到未知工具并恢复"),
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("测试未知工具")
    assert result["summary"] == "识别到未知工具并恢复"
    # 未知工具的错误观察应出现在对话里
    joined = " ".join(m.get("content", "") for m in result["conversation"])
    assert "不存在" in joined


async def test_max_steps_terminates(db_session, monkeypatch):
    monkeypatch.setattr(config, "MAX_STEPS", 3)
    # 始终要求调工具 → 必然撞上步数上限
    llm = FakeLLMClient(script=[_plan_json()] + [_think("echo", text="x")] * 10)
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("无限循环防护")
    # 循环被终止，给出了兜底回答
    assert result["summary"]
    acts = [s for s in result["steps"] if s["type"] == "act"]
    assert len(acts) <= 3
    row = await db_session.get(AgentSession, result["session_id"])
    assert row.status in ("completed", "abandoned")


async def test_invalid_json_retry_then_recover(db_session):
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            "这不是 JSON",                    # 第一次 THINK 解析失败
            _think("final", answer="重试后成功"),  # 纠正后成功
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("JSON 容错")
    assert result["summary"] == "重试后成功"


async def test_knowledge_state_updated(db_session):
    llm = FakeLLMClient(script=[_plan_json(), _think("final", answer="完成")])
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("复习操作系统第三章")
    # topic 取目标前 12 字
    row = await db_session.scalar(
        select(KnowledgeState).where(
            KnowledgeState.user_id == engine._user_id
        )
    )
    assert row is not None
    assert row.review_count == 1
    assert row.mastery_level > 0


async def test_eval_logs_written(db_session):
    llm = FakeLLMClient(
        script=[_plan_json(), _think("echo", text="a"), _think("final", answer="ok")]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session("评测落库")
    logs = (await db_session.scalars(
        select(EvalLog).where(EvalLog.session_id == result["session_id"])
    )).all()
    metrics = {log.metric for log in logs}
    assert {
        "task_completion_rate",
        "tool_call_success_rate",
        "avg_latency_ms",
        "plan_deviation_rate",
    } <= metrics


async def test_continue_session_multi_turn(db_session):
    # 注意：continue_session 会重新规划（planner 再消耗一条响应），
    # 所以脚本按「计划+回答」× 2 准备。
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            _think("final", answer="第一轮回答"),
            _plan_json(),
            _think("final", answer="第二轮回答"),
        ]
    )
    engine = await _make_engine(db_session, llm)
    first = await engine.start_session("多轮测试")
    second = await engine.continue_session(first["session_id"], "再问一个问题")
    assert second["summary"] == "第二轮回答"
    assert len(second["conversation"]) > len(first["conversation"])

# ==================== 冒烟复现回归测试 ====================


async def test_think_prose_then_recovers(db_session):
    """复现真实冒烟：Coder 模型先输出长分析文字再给 JSON，前两次解析失败，
    第三次成功 —— 引擎应恢复并继续执行，而不是放弃。"""
    prose = '好的，我已经检索到了相关笔记。接下来我需要对笔记进行结构化处理，建立对进程调度的整体认知。'
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            prose,                                   # think#1 失败（无 JSON）
            prose,                                   # think#2 失败
            _think('echo', text='恢复成功'),        # think#3 成功
            _think('final', answer='完成复习'),
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session('帮我复习操作系统')
    assert result['summary'] == '完成复习'
    acts = [s for s in result['steps'] if s['type'] == 'act']
    assert len(acts) == 1
    assert acts[0]['tool'] == 'echo'
    # 3 次 think 尝试都记录了吗？至少应有 think 步骤
    thinks = [s for s in result['steps'] if s['type'] == 'think']
    assert len(thinks) >= 1


async def test_all_think_fail_then_finalize_recovers(db_session):
    """复现冒烟根因：所有 think 尝试都失败 → finalize 第一次返回决策 JSON，
    第二次才给真正回答 —— 引擎应剥离决策 JSON 拿到回答。"""
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            '不是 JSON',                    # think#1
            '不是 JSON',                    # think#2
            '不是 JSON',                    # think#3 → 放弃循环
            _think('generate_summary', note_ids=['x']),  # finalize#1 仍输出决策 JSON
            '已完成复习。关键结论：进程调度是操作系统的核心。',  # finalize#2 真正回答
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session('帮我复习操作系统')
    # 最终回答必须是 finalize 第二次给的真实回答，而不是决策 JSON
    assert '进程调度是操作系统的核心' in result['summary']
    assert 'generate_summary' not in result['summary']


async def test_finalize_with_final_action_uses_answer(db_session):
    """finalize 返回 {action: final, params: {answer}} 时直接提取 answer。"""
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            'bad',  # think#1
            'bad',  # think#2
            'bad',  # think#3
            _think('final', answer='从决策中提取的回答'),
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session('测试')
    assert result['summary'] == '从决策中提取的回答'


async def test_observation_includes_format_reminder(db_session):
    """工具观察消息应附带『只输出 JSON 决策』提示（防止模型下一轮又啰嗦）。"""
    llm = FakeLLMClient(
        script=[
            _plan_json(),
            _think('echo', text='hi'),
            _think('final', answer='ok'),
        ]
    )
    engine = await _make_engine(db_session, llm)
    result = await engine.start_session('测试')
    obs_msgs = [m for m in result['conversation'] if '[工具 echo 返回]' in m.get('content', '')]
    assert obs_msgs
    assert '只输出一个 JSON 决策对象' in obs_msgs[0]['content']
