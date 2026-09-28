[English](README.md)丨简体中文

<div align="center">
  <h1>KnowWeave</h1>
  <p>用 Markdown 记学习笔记，再让 AI 助手读懂它们：写摘要、出题自测、讲解你没掌握的概念。</p>
  <p>
    <a href="#快速开始"><strong>快速开始</strong></a>
    ·
    <a href="docs/api.zh-Hans.md"><strong>API 文档</strong></a>
    ·
    <a href="docs/frontend-architecture.zh-Hans.md"><strong>架构说明</strong></a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
    <img src="https://img.shields.io/badge/python-3.10%2B-3776ab.svg" alt="Python 3.10 或更高">
    <img src="https://img.shields.io/badge/flutter-Material%203-02569b.svg" alt="Flutter 与 Material 3">
  </p>
</div>

KnowWeave 是一个面向学习场景的笔记应用。你用 Markdown 记录笔记（也可以导入 PDF、PPTX、Markdown 文件），然后与一个基于笔记内容推理的 AI 助手一起复习。

助手内部是一个 ReAct 循环：先规划几步，每轮调用一个工具，读取结果后继续，直到能给出答案。它可以按语义检索笔记、生成摘要、出选择题、解释你反复出错的概念，还能指出两篇笔记之间的关联。它的每一步都会被记录下来，因此你可以查看调用了哪些工具、每次耗時多久、以及实际执行与最初计划的偏离程度。

## 功能

**学习助手**

- 自研的 ReAct（推理与行动）循环，不依赖任何 Agent 框架。模型的决策是纯文本 JSON，因此任何兼容 OpenAI 接口的模型都能驱动它。
- 五个工具：`search_notes`、`generate_summary`、`create_quiz`、`cross_reference`、`explain_concept`。它们在同一个注册中心声明，注册中心同时生成模型选择工具时所读的描述。
- 答题结果回流为每篇笔记的掌握度，并记录需要重看的薄弱点。

**三层记忆**

- 短期：当前对话的最近若干轮。
- 长期：每篇笔记的掌握度与薄弱点，存于 SQLite，每次答题后更新。
- 语义：笔记分块在本地向量化，按向量相似度检索。

**检索**

- 一个上传接口接受 PDF、PPTX、Markdown；纯文本笔记在创建时即建立索引。
- 文档经解析、重叠分块、用 BGE（`BAAI/bge-small-zh-v1.5`）向量化后存入 ChromaDB。向量化在本地完成，不依赖外部服务。

**评测**

- 每一步都记录耗时与成败。
- 单次会话聚合为任务完成率、工具调用成功率、工具平均耗时、计划偏离率四项指标。

**模型**

- 一份 OpenAI 兼容的模型注册表，用一个环境变量切换。ModelScope、NVIDIA build、Moonshot 已预先配置好，接入其他端点只需改一个字典。

## 快速开始

### 后端

```bash
# 安装依赖（Python 3.10 或更高）
pip install -r backend/requirements.txt

# 创建配置，并填入你要使用的那个 provider 的 API key
cp backend/.env.example backend/.env

# 启动服务，Swagger 文档在 http://127.0.0.1:8000/docs
uvicorn backend.main:app --reload --port 8000
```

### 客户端

```bash
cd app
flutter pub get
flutter run

# 构建 release 包时指定后端地址
flutter build apk --dart-define=API_BASE_URL=http://<你的后端地址>:8000
```

界面默认跟随系统语言，可在「我的」页在英文与简体中文之间切换；助手会用与界面一致的语言回答，从 Prompt 到错误提示都随语言切换。

## 工作原理

一次「帮我复习操作系统第三章」的请求会经历四个阶段。

1. 规划器把目标拆成有序步骤。计划只是建议：助手可以偏离，偏离程度会被度量。
2. ReAct 循环每轮让模型输出一个 JSON 决策：它在想什么、调用哪个工具、参数是什么。引擎执行该工具，把观察结果追加到对话，再问下一轮。
3. 工具自然串起来：`search_notes` 找到相关笔记，`generate_summary` 建立整体认识，`create_quiz` 生成题目，`explain_concept` 补齐答题暴露出的薄弱概念。
4. 结果回写：掌握度与薄弱点更新，本次会话的评测记录落库。

循环是有边界的：单次会话最多 15 步，工具输出进入上下文前截断到 2000 字符，闲置超过 300 秒的会话标记为已放弃，工具调用失败会作为观察结果返回给模型而不是让整轮崩掉。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11、FastAPI、SQLAlchemy（异步）、SQLite（WAL 模式） |
| Agent | ReAct 循环、工具注册中心、三层记忆、评测追踪 |
| 检索 | ChromaDB、BGE-small-zh-v1.5 向量化、重叠分块 |
| 模型 | 任意兼容 OpenAI 接口的端点 |
| 客户端 | Flutter、Riverpod、go_router、Material 3 |

## 文档

| 文档 | 内容 |
|---|---|
| [docs/api.zh-Hans.md](docs/api.zh-Hans.md) | 接口、请求响应字段、评测指标 |
| [docs/frontend-architecture.zh-Hans.md](docs/frontend-architecture.zh-Hans.md) | 客户端分层、依赖注入、主题、从笔记到助手的流程 |

## 配置

配置位于 `backend/.env`，全部条目及注释见 `backend/.env.example`。

| 变量 | 说明 |
|---|---|
| `LLM_MODEL` | 使用模型注册表中的哪一项 |
| `MODELSCOPE_API_KEY`、`MOONSHOT_API_KEY`、`NVIDIA_API_KEY` | 对应 provider 的凭据，填一个即可 |
| `LLM_MIN_INTERVAL` | 两次调用之间的最小间隔秒数，用于限流较紧的 provider |
| `MAX_STEPS` | 单次会话最大步数（默认 15） |
| `LLM_TEMPERATURE` | 采样温度（默认 0.3） |
| `JWT_SECRET` | 访问令牌签名密钥，对外提供服务前请更换 |
| `EMBEDDING_MODEL` | 本地向量化模型（默认 `BAAI/bge-small-zh-v1.5`） |
| `CHUNK_SIZE`、`CHUNK_OVERLAP` | 文档分块参数 |

## 参与贡献

1. Fork 仓库并新建分支：`git checkout -b feat/short-description`。
2. 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)，一次提交只做一件逻辑上完整的事。
3. 提交 PR 前先跑测试：

```bash
cd backend && pytest
cd app && flutter test
```

4. 提交 PR，并说明改了什么、如何验证。

## 许可

MIT，详见 [LICENSE](LICENSE)。
