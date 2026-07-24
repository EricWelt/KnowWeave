"""答题闭环测试：POST /agent/sessions/{id}/answers 更新知识状态。"""
import json

import pytest
from sqlalchemy import select

from backend.models import AgentSession, KnowledgeState, User


async def _make_user_and_session(client, auth_headers, goal="帮我复习操作系统"):
    # 创建会话（走 API，FakeLLM 由 test_api_e2e 的 autouse fixture 提供）
    resp = await client.post(
        "/agent/sessions", headers=auth_headers, json={"goal": goal}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["session_id"]


async def test_submit_answers_updates_knowledge(client, auth_headers):
    session_id = await _make_user_and_session(client, auth_headers)

    resp = await client.post(
        f"/agent/sessions/{session_id}/answers",
        headers=auth_headers,
        json={
            "answers": [
                {
                    "question": "进程调度中 FCFS 的含义？",
                    "selected": "A. 先来先服务",
                    "correct": "A. 先来先服务",
                    "is_correct": True,
                },
                {
                    "question": "银行家算法用于？",
                    "selected": "A. 死锁检测",
                    "correct": "B. 死锁避免",
                    "is_correct": False,
                },
                {
                    "question": "周转时间 = ?",
                    "selected": "A. 完成时间 - 到达时间",
                    "correct": "A. 完成时间 - 到达时间",
                    "is_correct": True,
                },
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["correct"] == 2
    assert body["total"] == 3
    assert body["mastery_level"] > 0
    assert any("银行家算法" in w for w in body["weak_points"])


async def test_submit_answers_all_wrong_lowers_mastery(client, auth_headers):
    session_id = await _make_user_and_session(client, auth_headers)

    resp = await client.post(
        f"/agent/sessions/{session_id}/answers",
        headers=auth_headers,
        json={
            "answers": [
                {
                    "question": "Q1",
                    "selected": "A",
                    "correct": "B",
                    "is_correct": False,
                }
            ]
        },
    )
    body = resp.json()
    assert body["correct"] == 0
    # 会话创建时引擎已给 mastery 复习提升（+0.05），全错后按 EMA 打折：
    # 0.3*0.05 + 0.7*0 = 0.015 → 应显著低于复习提升值
    assert body["mastery_level"] < 0.05
    assert "Q1" in body["weak_points"]


async def test_submit_answers_requires_ownership(client, auth_headers, auth_headers_bob):
    session_id = await _make_user_and_session(client, auth_headers)

    resp = await client.post(
        f"/agent/sessions/{session_id}/answers",
        headers=auth_headers_bob,
        json={
            "answers": [
                {
                    "question": "Q",
                    "selected": "A",
                    "correct": "A",
                    "is_correct": True,
                }
            ]
        },
    )
    assert resp.status_code == 404


async def test_submit_answers_requires_auth(client):
    resp = await client.post("/agent/sessions/xxx/answers", json={"answers": []})
    assert resp.status_code == 401
