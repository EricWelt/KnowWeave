"""pytest 全局配置。

关键设计（学习点）：
1. 环境变量必须在 import backend 模块**之前**设置 —— 因为 config.py/database.py
   在导入时即读取路径并创建 engine。
2. 每个测试自动重建表（fresh_db autouse）保证隔离；
3. 通用测试禁用真实 RAG（不加载 BGE/不写 Chroma）——RAG 有专项测试；
4. 用 httpx.AsyncClient + ASGITransport 在纯内存中测 FastAPI。
"""
import os
import tempfile

import pytest
import pytest_asyncio

# ===== 必须在导入 backend 之前设置 =====
# ChromaDB 匿名遥测会 POST 到外网；沙箱网络异常时会导致挂起，测试环境关闭。
os.environ["ANONYMIZED_TELEMETRY"] = "False"
TEST_DIR = tempfile.mkdtemp(prefix="knowweave_test_")
os.environ["DATABASE_PATH"] = os.path.join(TEST_DIR, "test.sqlite")
os.environ["CHROMA_PATH"] = os.path.join(TEST_DIR, "chroma_db")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from backend.database import Base, _engine, init_db  # noqa: E402
from backend.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_rag(monkeypatch):
    """通用测试把 RAG 索引替换为 no-op（真实 RAG 在 test_rag/test_ingestion 专项验证）。"""

    async def fake_index(note, session=None):
        return []

    async def fake_remove(note_id, session=None):
        return None

    monkeypatch.setattr("backend.routers.notes.index_note", fake_index)
    monkeypatch.setattr("backend.routers.notes.remove_from_index", fake_remove)
    monkeypatch.setattr("backend.routers.upload.index_note", fake_index)


@pytest_asyncio.fixture(autouse=True)
async def fresh_db():
    """每个测试前重建全部表，保证互不污染。"""
    os.makedirs(os.path.dirname(os.environ["DATABASE_PATH"]), exist_ok=True)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db_session():
    """直接操作数据库 Session（引擎单测用）。"""
    from backend.database import async_session as _async_session

    async with _async_session() as s:
        yield s


async def _register_and_login(client, username: str, password: str = "secret123"):
    resp = await client.post(
        "/auth/register", json={"username": username, "password": password}
    )
    assert resp.status_code == 201, resp.text
    resp = await client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


@pytest_asyncio.fixture
async def auth_headers(client):
    return await _register_and_login(client, "alice")


@pytest_asyncio.fixture
async def auth_headers_bob(client):
    return await _register_and_login(client, "bob")
