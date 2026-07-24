"""认证模块测试：注册 / 登录 / 当前用户。"""
import pytest


async def test_register_success(client):
    resp = await client.post(
        "/auth/register", json={"username": "carol", "password": "pass123456"}
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "注册成功"


async def test_register_duplicate_username(client, auth_headers):
    resp = await client.post(
        "/auth/register", json={"username": "alice", "password": "pass123456"}
    )
    assert resp.status_code == 400
    assert "占用" in resp.json()["detail"]


async def test_register_invalid_payload(client):
    # 密码太短 → 422 校验失败
    resp = await client.post(
        "/auth/register", json={"username": "dave", "password": "123"}
    )
    assert resp.status_code == 422


async def test_login_success_returns_token(client):
    await client.post(
        "/auth/register", json={"username": "erin", "password": "pass123456"}
    )
    resp = await client.post(
        "/auth/login", json={"username": "erin", "password": "pass123456"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token"]
    assert body["user_id"]
    assert body["username"] == "erin"


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register", json={"username": "frank", "password": "pass123456"}
    )
    resp = await client.post(
        "/auth/login", json={"username": "frank", "password": "wrongpass"}
    )
    assert resp.status_code == 401


async def test_me_requires_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_with_valid_token(client, auth_headers):
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


async def test_me_with_invalid_token(client):
    resp = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401
