"""ReAct 推理循环主控（本项目核心）。

范式：THINK → ACT → OBSERVE → ... → FINAL_ANSWER

循环控制：
- max_steps 防无限循环（默认 15）
- 工具输出截断 TOOL_OUTPUT_MAX_CHARS（默认 2000）
- 会话超时 SESSION_TIMEOUT_SECONDS → 标记 abandoned
- 工具异常不崩溃：把错误作为 observation 继续

LLM 决策格式（provider 无关，纯文本 JSON，不依赖 function calling）：
{"thought": "分析", "action": "工具名" | "final", "params": {...}}
"""
import json
import time
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..models import AgentSession
from ..tools import ToolRegistry
from .eval_tracker import EvalTracker
from .json_utils import parse_json_defensive
from .llm_client import LLMClient
from .memory import MemoryManager
from .planner import Planner

THINK_SYSTEM = (
    "你是一个智能学习助手 Agent，采用 ReAct（推理+行动）范式帮用户完成学习任务。\n"
    "规则：\n"
    "1. 每轮输出一个 JSON 对象，格式："
    '{"thought": "对当前情况的简短分析", "action": "工具名或final", "params": {...}}\n'
    "2. action 只能是给出的工具名之一，或 final（任务完成时给出最终回答）。\n"
    "3. 调用工具时 params 必须符合工具参数要求。\n"
    "4. 观察工具返回后，再决定下一步；不要重复调用相同参数的同一工具。\n"
    "5. 任务完成时：{\"thought\": \"总结\", \"action\": \"final\", "
    '\"params\": {\"answer\": "给用户的最终回答(markdown)"}}\n'
    "只输出 JSON，不要任何额外文字。"
)


class AgentEngine:
    def __init__(
        self,
        session: AsyncSession,
        user_id: str,
        registry: ToolRegistry,
        llm: LLMClient,
        tracker: EvalTracker,
        memory: MemoryManager,
        planner: Planner,
    ):
        self._session = session
        self._user_id = user_id
        self._registry = registry
        self._llm = llm
        self._tracker = tracker
        self._memory = memory
        self._planner = planner

    # ================= 对外入口 =================

    async def start_session(self, goal: str) -> dict:
        """创建并执行一次完整 Agent 会话。"""
        row = AgentSession(user_id=self._user_id, goal=goal)
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return await self._execute(row, initial_user_message=goal)

    async def continue_session(self, session_id: str, message: str) -> dict:
        """在已有会话中继续对话（多轮交互）。"""
        row = await self._session.get(AgentSession, session_id)
        if row is None or row.user_id != self._user_id:
            raise ValueError("会话不存在")
        return await self._execute(row, initial_user_message=message)

    # ================= 主流程 =================

    async def _execute(self, row: AgentSession, initial_user_message: str) -> dict:
        start_time = time.monotonic()
        # 0) 绑定评测器到真实会话 id（start/continue 两条路径都走这里）
        self._tracker.attach(row.id)
        # 1) 加载记忆 + 规划
        knowledge_summary = await self._memory.load_knowledge_summary()
        tools_desc = self._registry.descriptions()
        plan = await self._planner.plan(
            initial_user_message, knowledge_summary, tools_desc
        )
        planned_tools = [p.get("tool") for p in plan if isinstance(p, dict)]

        # 2) 组装消息（system + 历史 + 当前用户消息）
        system_prompt = self._build_system_prompt(
            row.goal, knowledge_summary, plan
        )
        conversation: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]
        history = await self._memory.load_recent_conversation(row.id)
        # 历史里去掉旧的 system（重建）
        history = [m for m in history if m.get("role") != "system"]
        conversation.extend(history)
        conversation.append(
            {"role": "user", "content": initial_user_message}
        )

        final_answer = ""
        completed_steps = 0
        step_count = 0

        # 3) ReAct 循环
        while step_count < config.MAX_STEPS:
            elapsed = time.monotonic() - start_time
            if elapsed > config.SESSION_TIMEOUT_SECONDS:
                row.status = "abandoned"
                break

            # ---- THINK ----
            decision = await self._think(conversation, step_count)
            if decision is None:
                break  # 解析失败已重试过，兜底结束

            thought = decision.get("thought", "")
            await self._tracker.record_step(
                step_type="think", content=thought[:1000]
            )

            # ---- 决策分支 ----
            action = decision.get("action", "")
            if action == "final":
                final_answer = (
                    decision.get("params", {}).get("answer", "")
                    or decision.get("answer", "")
                )
                # 最终回答也进入对话历史（否则续聊时上下文缺失）
                if final_answer:
                    conversation.append(
                        {"role": "assistant", "content": final_answer}
                    )
                break
            if not action:
                break

            # ---- ACT ----
            tool = self._registry.get(action)
            if tool is None:
                observation = f"错误：工具「{action}」不存在。可用工具: {self._registry.descriptions()}"
                await self._tracker.record_step(
                    step_type="observe", content=observation, success=False
                )
                conversation.append(
                    {"role": "assistant", "content": f"调用工具 {action}"}
                )
                conversation.append({"role": "user", "content": observation})
                step_count += 1
                continue

            params = decision.get("params", {}) or {}
            t0 = time.monotonic()
            try:
                result = await tool.run(**params)
                latency_ms = int((time.monotonic() - t0) * 1000)
                await self._tracker.record_step(
                    step_type="act",
                    content=json.dumps(
                        {"tool": action, "params": params}, ensure_ascii=False
                    ),
                    tool_name=action,
                    latency_ms=latency_ms,
                    success=result.success,
                    error_message=result.error,
                )
                if result.success:
                    observation = json.dumps(result.data, ensure_ascii=False)
                else:
                    observation = f"工具执行失败: {result.error}"
            except Exception as e:  # noqa: BLE001 —— 工具抛异常也要记录并继续
                latency_ms = int((time.monotonic() - t0) * 1000)
                await self._tracker.record_step(
                    step_type="act",
                    content=json.dumps(
                        {"tool": action, "params": params}, ensure_ascii=False
                    ),
                    tool_name=action,
                    latency_ms=latency_ms,
                    success=False,
                    error_message=str(e),
                )
                observation = f"工具异常: {e}"

            # ---- OBSERVE（截断）----
            observation = observation[: config.TOOL_OUTPUT_MAX_CHARS]
            conversation.append(
                {"role": "assistant", "content": f"调用工具 {action}"}
            )
            conversation.append(
                {
                    "role": "user",
                    "content": f"[工具 {action} 返回]\n{observation}\n\n"
                    "请基于以上结果，只输出一个 JSON 决策对象，不要任何解释文字。",
                }
            )
            step_count += 1
            completed_steps += 1

        # 4) FINAL_ANSWER：若循环结束时还没有 final 回答，补一次总结
        if not final_answer:
            final_answer = await self._finalize_answer(conversation, plan)
        if not final_answer:
            final_answer = "已完成本轮学习任务（达到步数上限）。可继续追问更具体的问题。"
        if final_answer:
            completed_steps = max(completed_steps, 1)  # 有回答即视为任务有产出

        # 5) 落库：会话状态 + 对话历史
        row.status = "completed"
        row.conversation_json = json.dumps(conversation, ensure_ascii=False)
        await self._session.commit()

        # 6) 更新长期记忆（简化主题：取目标前 12 字作为 topic 粗粒度）
        topic = row.goal[:12]
        weak = self._extract_weak_points(conversation)
        await self._memory.update_knowledge(
            topic=topic, quiz_correct_count=0, quiz_total=0, weak_points=weak
        )

        # 7) 评测汇总
        eval_summary = await self._tracker.finalize_session(
            planned_tools=planned_tools,
            completed_steps=completed_steps,
            total_plan_steps=len(plan),
        )

        return {
            "session_id": row.id,
            "summary": final_answer,
            "plan": plan,
            "steps": await self._steps_summary(row.id),
            "eval": eval_summary,
            "weak_points": weak,
            "conversation": conversation,
        }

    # ================= 内部方法 =================

    def _build_system_prompt(
        self, goal: str, knowledge_summary: str, plan: list[dict]
    ) -> str:
        plan_text = (
            "\n".join(
                f"{p.get('step')}. {p.get('action')}"
                + (f"（工具: {p.get('tool')}）" if p.get("tool") else "")
                for p in plan
            )
            if plan
            else "（无预规划，自行安排步骤）"
        )
        return (
            f"{THINK_SYSTEM}\n\n"
            f"## 本次学习目标\n{goal}\n\n"
            f"## 参考执行计划（仅供参考，可调整）\n{plan_text}\n\n"
            f"## 用户知识状态\n{knowledge_summary or '（暂无记录）'}\n\n"
            f"## 可用工具\n{self._registry.descriptions()}"
        )

    async def _think(
        self, conversation: list[dict], step_count: int
    ) -> dict | None:
        """THINK 步骤：LLM 输出决策 JSON。

        真实踩坑（冒烟诊断）：Coder 类模型爱先写一段分析再输出 JSON，
        max_tokens 不足时结尾的 } 被截断导致解析失败。对策：
        - max_tokens 给足（1536），避免截断；
        - 重试 3 次且提示逐级加严（从"只输出 JSON"到"禁止任何解释文字"）。
        """
        corrections = [
            '输出格式错误（第1次）。请只输出一个 JSON 对象：'
            '{"thought": "...", "action": "工具名|final", "params": {...}}，不要任何解释文字。',
            '第2次格式错误。你的上一条输出里混入了非 JSON 内容或 JSON 不完整。'
            '现在只允许输出一个合法 JSON 对象（以 { 开头、以 } 结尾），禁止输出任何其他字符。',
            '第3次格式错误。请直接输出决策 JSON：{"thought": "分析", '
            '"action": "工具名或final", "params": {...}}。不要输出任何其他内容。',
        ]
        for attempt in range(3):
            try:
                text = await self._llm.chat(conversation, max_tokens=1536)
                data = parse_json_defensive(text)
                if isinstance(data, dict) and data.get("action"):
                    return data
                conversation.append(
                    {"role": "user", "content": corrections[attempt]}
                )
            except Exception as e:  # noqa: BLE001
                conversation.append(
                    {
                        "role": "user",
                        "content": f"你的输出不是合法 JSON（第{attempt+1}次）: {str(e)[:120]}。"
                        + corrections[attempt],
                    }
                )
        return None

    async def _finalize_answer(
        self, conversation: list[dict], plan: list[dict]
    ) -> str:
        """循环因步数/超时/解析失败结束时，让 LLM 基于已有观察生成总结。

        真实踩坑：LLM 在循环被中断时可能仍在"思考下一步"，把决策 JSON
        （如 action=generate_summary）当作回答返回。对策：检测到决策 JSON 时
        追加一次强制"给用户回答"的调用；若仍输出 JSON，剥离后兜底。
        """
        instructions = [
            "基于以上过程，请用 markdown 给出最终回答：已完成哪些步骤、"
            "关键结论、对用户下一步复习的建议。直接给用户可读的回答，不要输出 JSON。",
            "请只输出给用户的最终回答（markdown 文本）。不要输出任何 JSON 对象、"
            "工具调用或决策格式。",
        ]
        text = ""
        for instruction in instructions:
            try:
                text = await self._llm.chat(
                    conversation
                    + [{"role": "user", "content": instruction}]
                )
                text = text.strip()
            except Exception:  # noqa: BLE001
                return ""
            # 若仍输出决策 JSON（模型还在想调工具），用更强的指令再来一次
            try:
                data = parse_json_defensive(text)
                if isinstance(data, dict) and data.get("action"):
                    if data.get("action") == "final":
                        ans = (data.get("params") or {}).get("answer") or data.get("answer")
                        if ans:
                            return ans
                    continue  # 模型还在决策 → 换更强的指令
            except ValueError:
                pass  # 不是 JSON → 正常回答，直接返回
            return text
        return ""

    def _extract_weak_points(self, conversation: list[dict]) -> list[str]:
        """简化实现：从 quiz 类工具返回中找含「错误」的线索（完整版可接用户作答分析）。"""
        weak = []
        for msg in conversation:
            content = msg.get("content", "")
            if "[工具 create_quiz 返回]" in content:
                try:
                    data = json.loads(content.split("]\n", 1)[1])
                    for q in data.get("questions", []):
                        if q.get("explanation") and "易错" in q["explanation"]:
                            weak.append(q.get("question", "")[:30])
                except Exception:  # noqa: BLE001
                    continue
        return list(dict.fromkeys(weak))[:5]

    async def _steps_summary(self, session_id: str) -> list[dict]:
        """把 agent_steps 压缩成 API 返回的步骤摘要。"""
        from sqlalchemy import select

        from ..models import AgentStep

        result = await self._session.scalars(
            select(AgentStep)
            .where(AgentStep.session_id == session_id)
            .order_by(AgentStep.step_index)
        )
        steps = []
        for i, s in enumerate(result.all(), start=1):
            summary = ""
            if s.step_type == "think":
                # 思考过程给足内容（前端可折叠展示「深度思考」）
                summary = s.content[:500]
            elif s.step_type == "act":
                summary = f"调用工具 {s.tool_name}"
                if not s.success:
                    summary += f"（失败: {s.error_message}）"
            else:
                summary = s.content[:200]
            steps.append(
                {
                    "step": i,
                    "type": s.step_type,
                    "summary": summary,
                    "tool": s.tool_name,
                }
            )
        return steps
