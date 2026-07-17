"""SQLite 异步引擎 + Session 管理。

设计要点：
- aiosqlite 而非同步 sqlite3：FastAPI async 路由里同步 IO 会阻塞事件循环；
- WAL 模式：允许并发读（Agent 推理循环中检索笔记与写日志可能同时发生）；
- foreign_keys=ON：虽然业务外键按 ID 关联，仍开启防止脏数据。
"""
import os

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from . import config


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


# SQLite 文件路径含 Windows 反斜杠，需转换为 URI 兼容形式
_db_path = config.DATABASE_PATH.replace("\\", "/")
_engine = create_async_engine(
    f"sqlite+aiosqlite:///{_db_path}",
    echo=False,
)


@event.listens_for(_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """每个新连接建立时执行 PRAGMA（aiosqlite 的 sync 引擎事件）。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")   # 并发读优化
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async_session = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """应用启动时建表；目录不存在则创建。"""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.UPLOAD_TEMP_DIR, exist_ok=True)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    """FastAPI 依赖：每个请求一个 Session。"""
    async with async_session() as session:
        yield session
