"""评测追踪器。

职责：会话过程中记录每步（think/act/observe），结束后计算量化指标并写 eval_logs。

指标：
- task_completion_rate: 完成的计划步骤 / 计划总步数（无计划时取 1.0 或由 engine 判定）
- tool_call_success_rate: 成功工具调用 / 总工具调用
- avg_latency_ms: 所有工具调用平均耗时
- plan_deviation_rate: 实际调用工具集合与计划工具集合的差异程度
"""
import json

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AgentStep, EvalLog


class EvalTracker:
    def __init__(self, session: AsyncSession, session_id: str = ""):
        self._session = session
        self._session_id = session_id
        self._step_index = 0

    def attach(self, session_id: str) -> None:
        """把 tracker 绑定到真实会话 id（engine 创建会话行后调用）。"""
        self._session_id = session_id

    async def record_step(
        self,
        step_type: str,
        content: str,
        tool_name: str | None = None,
        latency_ms: int = 0,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """写一条 agent_steps 记录。"""
        step = AgentStep(
            session_id=self._session_id,
            step_index=self._step_index,
            step_type=step_type,
            content=content,
            tool_name=tool_name,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
        )
        self._session.add(step)
        self._step_index += 1
        await self._session.commit()

    async def finalize_session(
        self,
        planned_tools: list[str],
        completed_steps: int,
        total_plan_steps: int,
    ) -> dict:
        """计算汇总指标、写入 eval_logs，返回指标字典。"""
        # 从 agent_steps 聚合
        steps = await self._get_steps()
        acts = [s for s in steps if s.step_type == "act" and s.tool_name]
        successful_acts = [s for s in acts if s.success]
        latencies = [s.latency_ms for s in acts if s.latency_ms > 0]

        executed_tools = {s.tool_name for s in acts}
        planned_set = {t for t in planned_tools if t}

        metrics = {
            "task_completion_rate": (
                completed_steps / total_plan_steps
                if total_plan_steps > 0
                else (1.0 if completed_steps > 0 else 0.0)
            ),
            "tool_call_success_rate": (
                len(successful_acts) / len(acts) if acts else 0.0
            ),
            "avg_latency_ms": (
                sum(latencies) / len(latencies) if latencies else 0.0
            ),
            "plan_deviation_rate": (
                len(planned_set - executed_tools) / len(planned_set)
                if planned_set
                else 0.0
            ),
        }

        for metric, value in metrics.items():
            self._session.add(
                EvalLog(
                    session_id=self._session_id,
                    metric=metric,
                    value=round(value, 4),
                    detail_json=json.dumps(
                        {
                            "executed_tools": sorted(executed_tools),
                            "planned_tools": sorted(planned_set),
                        },
                        ensure_ascii=False,
                    ),
                )
            )
        await self._session.commit()
        return metrics

    async def _get_steps(self) -> list[AgentStep]:
        from sqlalchemy import select

        result = await self._session.scalars(
            select(AgentStep)
            .where(AgentStep.session_id == self._session_id)
            .order_by(AgentStep.step_index)
        )
        return list(result.all())
