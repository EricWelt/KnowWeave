"""笔记 CRUD 测试：创建/列表/详情/编辑/删除/搜索/归属隔离。"""
import pytest


async def _create_note(client, headers, title="测试笔记", content="# 标题\n正文内容"):
    return await client.post(
        "/notes",
        headers=headers,
        json={"title": title, "content": content},
    )


async def test_create_note(client, auth_headers):
    resp = await _create_note(client, auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "测试笔记"
    assert body["content"] == "# 标题\n正文内容"
    assert body["source_type"] == "manual"


async def test_list_notes_returns_only_own(client, auth_headers, auth_headers_bob):
    await _create_note(client, auth_headers, title="Alice 的笔记")
    await _create_note(client, auth_headers_bob, title="Bob 的笔记")

    resp = await client.get("/notes", headers=auth_headers)
    titles = [n["title"] for n in resp.json()]
    assert titles == ["Alice 的笔记"]
    assert "Bob 的笔记" not in titles


async def test_get_note_detail(client, auth_headers):
    created = await _create_note(client, auth_headers)
    note_id = created.json()["id"]

    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == note_id


async def test_cannot_access_others_note(client, auth_headers, auth_headers_bob):
    created = await _create_note(client, auth_headers)
    note_id = created.json()["id"]

    resp = await client.get(f"/notes/{note_id}", headers=auth_headers_bob)
    assert resp.status_code == 404


async def test_update_note(client, auth_headers):
    created = await _create_note(client, auth_headers)
    note_id = created.json()["id"]

    resp = await client.put(
        f"/notes/{note_id}",
        headers=auth_headers,
        json={"title": "改名了", "content": "新内容"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "改名了"
    assert resp.json()["content"] == "新内容"


async def test_delete_note(client, auth_headers):
    created = await _create_note(client, auth_headers)
    note_id = created.json()["id"]

    resp = await client.delete(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 404


async def test_search_filter(client, auth_headers):
    await _create_note(client, auth_headers, title="操作系统-进程调度")
    await _create_note(client, auth_headers, title="计算机网络-传输层")

    resp = await client.get("/notes?search=进程", headers=auth_headers)
    titles = [n["title"] for n in resp.json()]
    assert titles == ["操作系统-进程调度"]


async def test_notes_require_auth(client):
    resp = await client.get("/notes")
    assert resp.status_code == 401

async def test_reindex_endpoint(client, auth_headers):
    created = await _create_note(client, auth_headers, title='待重建索引')
    note_id = created.json()["id"]

    resp = await client.post(f"/notes/{note_id}/reindex", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == note_id


async def test_reindex_requires_ownership(client, auth_headers, auth_headers_bob):
    created = await _create_note(client, auth_headers)
    note_id = created.json()["id"]

    resp = await client.post(f"/notes/{note_id}/reindex", headers=auth_headers_bob)
    assert resp.status_code == 404
