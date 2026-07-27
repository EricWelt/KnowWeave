"""CLI 冒烟测试：用真实 LLM 跑一次完整 Agent 会话（需要已配置 .env 的 API key）。

用法: python scripts/run_agent_demo.py "帮我复习操作系统第三章"
"""
import argparse
import asyncio
import os
import sys

# 把仓库根目录加入 sys.path（脚本以包方式导入 backend.*）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("goal", nargs="?", default="帮我复习操作系统的进程调度")
    args = parser.parse_args()

    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    from backend.database import async_session, init_db
    from backend.models import User
    from backend.agent.engine import AgentEngine
    from backend.agent.eval_tracker import EvalTracker
    from backend.agent.llm_client import LLMClient
    from backend.agent.memory import MemoryManager
    from backend.agent.planner import Planner
    from backend.tools import build_registry

    await init_db()
    async with async_session() as session:
        from sqlalchemy import select
        user = await session.scalar(select(User).where(User.username == "demo"))
        if user is None:
            print("请先运行 scripts/seed_demo_notes.py 创建 demo 用户")
            return

        llm = LLMClient()
        print(f"[llm] provider={llm.provider} model={llm.model}")
        registry = build_registry(session, user.id, llm)
        tracker = EvalTracker(session, session_id="")
        memory = MemoryManager(session, user.id)
        planner = Planner(llm)
        engine = AgentEngine(session, user.id, registry, llm, tracker, memory, planner)

        print(f"\n>>> 目标: {args.goal}\n")
        result = await engine.start_session(args.goal)

        print("=== 计划 ===")
        for p in result["plan"]:
            print(f"  {p.get('step')}. {p.get('action')} (工具: {p.get('tool')})")
        print("\n=== 执行步骤 ===")
        for s in result["steps"]:
            print(f"  [{s['type']}] {s['summary']}")
        print("\n=== 最终回答 ===")
        print(result["summary"])
        print("\n=== 评测 ===")
        for k, v in result["eval"].items():
            print(f"  {k}: {v}")
        print("\n=== 薄弱点 ===")
        print("  " + "、".join(result["weak_points"]) if result["weak_points"] else "  （无）")


if __name__ == "__main__":
    asyncio.run(main())
