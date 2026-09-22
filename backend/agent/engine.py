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
from string import Template

from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from ..models import AgentSession
from ..tools import ToolRegistry
from .eval_tracker import EvalTracker
from .json_utils import parse_json_defensive
from .llm_client import LLMClient
from .memory import MemoryManager
from .planner import Planner
from .prompts import get_texts


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
        lang: str | None = None,
    ):
        self._session = session
        self._user_id = user_id
        self._registry = registry
        self._llm = llm
        self._tracker = tracker
        self._memory = memory
        self._planner = planner
        # 进入模型上下文的自然语言文本（按语言选择；见 agent/prompts/）
        self._texts = get_texts(lang or config.AGENT_DEFAULT_LANG)

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
            raise ValueError(self._texts["err_session_missing"])
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
                observation = Template(
                    self._texts["obs_tool_missing"]
                ).substitute(tool=action, tools=self._registry.descriptions())
                await self._tracker.record_step(
                    step_type="observe", content=observation, success=False
                )
                conversation.append(
                    {
                        "role": "assistant",
                        "content": Template(
                            self._texts["note_tool_call"]
                        ).substitute(tool=action),
                    }
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
                    observation = Template(
                        self._texts["obs_tool_failed"]
                    ).substitute(error=result.error)
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
                observation = Template(self._texts["obs_tool_error"]).substitute(
                    error=e
                )

            # ---- OBSERVE（截断）----
            observation = observation[: config.TOOL_OUTPUT_MAX_CHARS]
            conversation.append(
                {
                    "role": "assistant",
                    "content": Template(self._texts["note_tool_call"]).substitute(
                        tool=action
                    ),
                }
            )
            conversation.append(
                {
                    "role": "user",
                    # 「[工具 X 返回]」是前后端共用的协议常量，不随语言变化；
                    # 其后的提醒语按当前语言给出。
                    "content": f"[工具 {action} 返回]\n{observation}\n\n"
                    f"{self._texts['obs_reminder']}",
                }
            )
            step_count += 1
            completed_steps += 1

        # 4) FINAL_ANSWER：若循环结束时还没有 final 回答，补一次总结
        if not final_answer:
            final_answer = await self._finalize_answer(conversation, plan)
        if not final_answer:
            final_answer = self._texts["answer_fallback"]
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
        texts = self._texts
        tool_suffix = Template(texts["plan_tool_suffix"])
        plan_text = (
            "\n".join(
                f"{p.get('step')}. {p.get('action')}"
                + (
                    tool_suffix.substitute(tool=p.get("tool"))
                    if p.get("tool")
                    else ""
                )
                for p in plan
            )
            if plan
            else texts["plan_empty"]
        )
        return (
            f"{texts['think_system']}\n\n"
            f"{texts['plan_goal_header']}\n{goal}\n\n"
            f"{texts['plan_plan_header']}\n{plan_text}\n\n"
            f"{texts['plan_knowledge_header']}\n"
            f"{knowledge_summary or texts['none_recorded']}\n\n"
            f"{texts['plan_tools_header']}\n{self._registry.descriptions()}"
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
        texts = self._texts
        corrections = [
            texts["correction_1"],
            texts["correction_2"],
            texts["correction_3"],
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
                        "content": Template(
                            texts["correction_parse_error"]
                        ).substitute(attempt=attempt + 1, error=str(e)[:120])
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
            self._texts["finalize_1"],
            self._texts["finalize_2"],
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
        markers = [
            m.strip() for m in self._texts["weak_markers"].split("|") if m.strip()
        ]
        weak = []
        for msg in conversation:
            content = msg.get("content", "")
            # 协议常量：与后端写入、前端解析保持一致，不随语言变化
            if "[工具 create_quiz 返回]" in content:
                try:
                    data = json.loads(content.split("]\n", 1)[1])
                    for q in data.get("questions", []):
                        explanation = q.get("explanation") or ""
                        if any(marker in explanation for marker in markers):
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
                summary = Template(self._texts["step_summary_tool"]).substitute(
                    tool=s.tool_name
                )
                if not s.success:
                    summary += Template(
                        self._texts["step_summary_failed"]
                    ).substitute(error=s.error_message)
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
