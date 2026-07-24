"""文件上传 API 测试：认证/类型校验/解析/入库（RAG 用 no-op 替身）。"""
import pytest

from tests.fixture_files import (
    make_garbage_bytes,
    make_markdown_bytes,
    make_pdf_bytes,
    make_pptx_bytes,
)


@pytest.fixture
def index_spy(monkeypatch):
    """记录 upload 路由是否调用 index_note（覆盖 conftest 的 no-op）。"""
    calls = []

    async def fake_index(note, session=None):
        calls.append((note.id, note.title))
        return []

    monkeypatch.setattr("backend.routers.upload.index_note", fake_index)
    return calls


async def _upload(client, headers, filename: str, content: bytes):
    return await client.post(
        "/upload",
        headers=headers,
        files={"file": (filename, content)},
    )


async def test_upload_requires_auth(client):
    resp = await _upload(client, {}, "note.md", b"# hi")
    assert resp.status_code == 401


async def test_upload_rejects_unsupported_extension(client, auth_headers):
    resp = await _upload(client, auth_headers, "data.docx", b"x" * 10)
    assert resp.status_code == 400
    assert "不支持" in resp.json()["detail"]


async def test_upload_rejects_empty_file(client, auth_headers):
    resp = await _upload(client, auth_headers, "empty.md", b"")
    assert resp.status_code == 400


async def test_upload_rejects_garbage_pdf(client, auth_headers):
    resp = await _upload(client, auth_headers, "fake.pdf", make_garbage_bytes())
    assert resp.status_code == 400


async def test_upload_markdown_success(client, auth_headers, index_spy):
    resp = await _upload(client, auth_headers, "note.md", make_markdown_bytes())
    assert resp.status_code == 201
    body = resp.json()
    assert body["note_id"]

    # 笔记已创建且触发索引
    note_id = body["note_id"]
    assert (note_id, "note.md") in index_spy

    # 通过笔记接口可见，source_type=markdown
    detail = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["source_type"] == "markdown"
    assert detail.json()["source_name"] == "note.md"
    assert "PCB" in detail.json()["content"]


async def test_upload_pdf_success(client, auth_headers, index_spy):
    resp = await _upload(client, auth_headers, "os.pdf", make_pdf_bytes())
    assert resp.status_code == 201
    assert resp.json()["note_id"]


async def test_upload_pptx_success(client, auth_headers, index_spy):
    resp = await _upload(client, auth_headers, "slides.pptx", make_pptx_bytes())
    assert resp.status_code == 201
    assert resp.json()["note_id"]
