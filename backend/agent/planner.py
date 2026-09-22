"""任务规划器。

输入：用户学习目标 + 知识状态摘要 + 可用工具描述
输出：步骤列表 [{step, action, tool}]（JSON）

设计要点：
- 计划是「建议」不是「强制」：engine 注入 system_prompt，LLM 在 think 阶段参考但不盲从；
- 防御性解析：LLM 输出 JSON 不稳定，用 chat_json 兜底；shape 校验失败则降级为空计划。
"""
from string import Template

from .. import config
from .llm_client import LLMClient
from .prompts import get_texts


class Planner:
    def __init__(self, llm: LLMClient, lang: str | None = None):
        self._llm = llm
        self._texts = get_texts(lang or config.AGENT_DEFAULT_LANG)

    async def plan(
        self,
        goal: str,
        knowledge_summary: str,
        tools_description: str,
    ) -> list[dict]:
        """返回步骤列表；失败时返回 []（engine 可无计划运行）。"""
        if not goal.strip():
            return []

        user = Template(self._texts["planner_user"]).substitute(
            goal=goal,
            knowledge=knowledge_summary or self._texts["none_recorded"],
            tools=tools_description or self._texts["none_available"],
        )
        try:
            data = await self._llm.chat_json(
                [
                    {"role": "system", "content": self._texts["planner_system"]},
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
