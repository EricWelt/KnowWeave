"""KnowWeave 后端入口。

启动: uvicorn main:app --reload --port 8000
文档: http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import agent, auth, notes, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动：建表（后续还会初始化 ChromaDB / Embedding）。"""
    await init_db()
    yield


app = FastAPI(
    title="KnowWeave AI Agent 学习系统",
    description="自研 ReAct Agent 智能学习后端",
    version="0.2.0",
    lifespan=lifespan,
)

# 允许局域网内 Flutter 客户端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(upload.router)
app.include_router(agent.router)


@app.get("/")
async def root():
    return {"msg": "KnowWeave backend is running!"}
