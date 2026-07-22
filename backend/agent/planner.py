"""任务规划器。

输入：用户学习目标 + 知识状态摘要 + 可用工具描述
输出：步骤列表 [{step, action, tool}]（JSON）

设计要点：
- 计划是「建议」不是「强制」：engine 注入 system_prompt，LLM 在 think 阶段参考但不盲从；
- 防御性解析：LLM 输出 JSON 不稳定，用 chat_json 兜底；shape 校验失败则降级为空计划。
"""
from .. import config
from .llm_client import LLMClient

PLANNER_SYSTEM = (
    "你是一位学习规划专家。根据用户的学习目标制定分步执行计划。\n"
    "只输出 JSON 数组，每项格式：\n"
    '[{"step": 1, "action": "具体行动描述", "tool": "建议使用的工具名或 null"}]\n'
    "工具名只能从给出的可用工具中选择，也可以为 null（表示该步骤不需要工具）。"
    "不要输出任何额外文字。"
)


class Planner:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    async def plan(
        self,
        goal: str,
        knowledge_summary: str,
        tools_description: str,
    ) -> list[dict]:
        """返回步骤列表；失败时返回 []（engine 可无计划运行）。"""
        if not goal.strip():
            return []

        user = (
            f"学习目标：{goal}\n\n"
            f"用户当前知识状态摘要：\n{knowledge_summary or '（暂无记录）'}\n\n"
            f"可用工具：\n{tools_description or '（无）'}\n\n"
            f"请输出 3-6 步的执行计划。"
        )
        try:
            data = await self._llm.chat_json(
                [
                    {"role": "system", "content": PLANNER_SYSTEM},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                max_tokens=config.MAX_STEPS * 80,
            )
            if not isinstance(data, list):
                return []
            # 清洗：只保留合法形状的步骤
            cleaned = []
            for item in data:
                if isinstance(item, dict) and item.get("action"):
                    cleaned.append(
                        {
                            "step": item.get("step", len(cleaned) + 1),
                            "action": item["action"],
                            "tool": item.get("tool"),
                        }
                    )
            return cleaned
        except Exception as e:  # noqa: BLE001
            print(f"[planner] 规划失败，降级为空计划: {e}")
            return []
