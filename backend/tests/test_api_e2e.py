"""端到端 API 测试：注册→登录→笔记→上传→Agent 对话（LLM 用假客户端）。

证明整条链路（路由→引擎→存储）是通的，同时不依赖真实 LLM。
"""
import json

import pytest

from backend.agent.json_utils import parse_json_defensive
from backend.agent.llm_client import LLMClient


class FakeLLM(LLMClient):
    def __init__(self):
        self.n = 0

    async def chat(self, messages, **kwargs):
        self.n += 1
        if self.n == 1:  # planner 调用
            return json.dumps(
                [{"step": 1, "action": "搜索相关笔记", "tool": "search_notes"}]
            )
        if self.n == 2:  # THINK：调 search_notes
            return json.dumps(
                {"thought": "先搜索", "action": "search_notes", "params": {"query": "进程调度"}}
            )
        return json.dumps(
            {"thought": "完成", "action": "final", "params": {"answer": "复习完成！"}}
        )

    async def chat_json(self, messages, **kwargs):
        return parse_json_defensive(await self.chat(messages, **kwargs))


@pytest.fixture(autouse=True)
def _fake_llm(monkeypatch):
    """把路由模块里的 LLMClient 换成 FakeLLM（注：build_registry 里也用了它）。"""
    monkeypatch.setattr("backend.routers.agent.LLMClient", FakeLLM)
    monkeypatch.setattr("backend.tools.LLMClient", FakeLLM)


async def test_full_chain_register_login_note_agent(client, auth_headers):
    # 1) 创建笔记
    resp = await client.post(
        "/notes",
        headers=auth_headers,
        json={"title": "操作系统", "content": "进程调度与内存管理"},
    )
    assert resp.status_code == 201
    note_id = resp.json()["id"]

    # 2) 列出笔记
    resp = await client.get("/notes", headers=auth_headers)
    assert len(resp.json()) == 1

    # 3) 查看详情
    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 200

    # 4) 发起 Agent 会话（LLM 是假的）
    resp = await client.post(
        "/agent/sessions",
        headers=auth_headers,
        json={"goal": "帮我复习操作系统"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["session_id"]
    assert body["summary"]
    assert isinstance(body["plan"], list)
    assert isinstance(body["steps"], list)
    assert body["eval"]["tool_call_success_rate"] is not None

    # 5) 查询会话详情与评测
    sid = body["session_id"]
    resp = await client.get(f"/agent/sessions/{sid}", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["conversation"]) > 0

    resp = await client.get(f"/agent/sessions/{sid}/eval", headers=auth_headers)
    assert resp.status_code == 200
    assert "task_completion_rate" in resp.json()["metrics"]

    # 6) 继续对话
    resp = await client.post(
        f"/agent/sessions/{sid}/chat",
        headers=auth_headers,
        json={"message": "进程调度不太懂"},
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


async def test_agent_requires_auth(client):
    resp = await client.post(
        "/agent/sessions", json={"goal": "x"}
    )
    assert resp.status_code == 401


async def test_agent_empty_goal(client, auth_headers):
    resp = await client.post(
        "/agent/sessions", headers=auth_headers, json={"goal": "   "}
    )
    assert resp.status_code == 400
