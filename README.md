# KnowWeave

> 知脉笔记（KnowWeave） —— 从「笔记应用 + LLM 封装」升级为**以自研 ReAct Agent 为核心的智能学习系统**。

KnowWeave 是一个面向学习场景的智能笔记 + AI 复习系统：管理 Markdown 笔记，并由一个自研的
ReAct（Reasoning + Acting）Agent 帮助你完成**检索笔记 → 生成摘要 → 出题自测 → 概念解释 →
跨笔记关联**的完整复习闭环。

## ✨ 特性

- **自研 ReAct Agent 引擎**（不依赖 LangChain/LangGraph）：THINK → ACT → OBSERVE 循环，支持任务规划、动态调整、多轮对话
- **三层记忆架构**：短期（对话历史）· 长期（SQLite 知识掌握状态 mastery/薄弱点追踪）· 语义（ChromaDB 向量检索）
- **RAG 全链路**：PDF/PPTX/Markdown 解析 → 文档分块 → BGE 本地向量化 → 语义检索
- **5 个可组合工具**：search_notes / generate_summary / create_quiz / cross_reference / explain_concept（ToolRegistry 统一注册）
- **可评测可观测**：每步记录耗时/成败，聚合任务完成率、工具调用成功率等指标；完整对话落库
- **多模型可选**：OpenAI 兼容模型注册表，一行切换（ModelScope Qwen / NVIDIA GLM、MiniMax / Kimi Moonshot）
- **现代 Flutter 前端**：Riverpod + go_router 分层架构，Material 3 主题（亮/暗），Android/iOS/Web

## 🏗️ 架构

```
Flutter (app/) ←REST + JWT→ FastAPI (backend/)
                              ├── REST: /auth /notes /upload /agent
                              ├── Agent 引擎: planner / memory / eval_tracker / ReAct engine
                              ├── 工具集: 5 个 Tool（ToolRegistry）
                              ├── RAG: chunker → BGE embedding → ChromaDB
                              └── 存储: SQLite（7 表）+ ChromaDB
```

## 📦 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy(async) + SQLite(WAL) · ChromaDB · BGE-small-zh-v1.5 |
| Agent | 自研 ReAct 引擎 · ToolRegistry · 三层记忆 · 评测追踪 |
| LLM | OpenAI SDK 兼容多 provider（ModelScope / NVIDIA build / Moonshot），模型注册表可扩展 |
| 前端 | Flutter · Riverpod · go_router · Material 3 |

## 🚀 快速开始

### 后端

```bash
# 1. 安装依赖（Python 3.10+）
pip install -r backend/requirements.txt

# 2. 配置（填入 LLM API key）
cp backend/.env.example backend/.env

# 3. 启动（Swagger: http://127.0.0.1:8000/docs）
uvicorn backend.main:app --reload --port 8000
```

### 前端

```bash
cd app
flutter pub get
flutter run
# 构建真机 APK（后端地址通过 --dart-define 注入）
flutter build apk --dart-define=API_BASE_URL=http://<你的后端地址>:8000
```

## 🧠 Agent 怎么工作

一次「帮我复习操作系统第三章」：

1. **Planner** 生成执行计划（建议非强制）
2. **ReAct 循环**：LLM 每轮输出 JSON 决策（思考/工具/参数）→ 引擎调度工具 → 观察结果回填上下文 → 继续
3. 工具链：`search_notes` 检索相关笔记 → `generate_summary` 建立认知 → `create_quiz` 出题自测 → `explain_concept` 解释薄弱概念
4. **记忆更新**：作答结果回流到知识掌握状态（mastery / 薄弱点）
5. **评测落库**：任务完成率、工具成功率、平均延迟等指标

## 🔌 API 概览

| 模块 | 端点 |
|---|---|
| 认证 | POST /auth/register · /auth/login · GET /auth/me |
| 笔记 | GET/POST /notes · GET/PUT/DELETE /notes/{id} · POST /notes/{id}/reindex |
| 上传 | POST /upload（PDF/PPTX/MD，自动解析+向量化） |
| Agent | POST /agent/sessions · /agent/sessions/{id}/chat · GET /agent/sessions · /{id}/eval |
| 答题闭环 | POST /agent/sessions/{id}/answers |

详细契约见 [docs/api.md](docs/api.md)，架构设计见 [docs/frontend-architecture.md](docs/frontend-architecture.md)。

## 🧪 测试

```bash
# 后端（81 用例：认证/笔记/上传/RAG/工具/Agent 流程/限流/防御解析）
cd backend && pytest -v

# 前端（Widget 测试 + 单元测试）
cd app && flutter test
```

## 📄 文档

- [docs/api.md](docs/api.md) — 后端 API 契约
- [docs/frontend-architecture.md](docs/frontend-architecture.md) — 前端架构（Riverpod/go_router/MD3/玻璃质感/思考过程展示）

## ⚖️ License

MIT
