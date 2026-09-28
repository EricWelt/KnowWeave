[English](api.md)丨简体中文

# KnowWeave 后端 API 文档

> 基础地址：`http://localhost:8000` · 交互式文档：`/docs`
> 认证：除 `/auth/register` 与 `/auth/login` 外，所有接口都需要请求头 `Authorization: Bearer <token>`。

## 语言

接口按请求指定的语言返回内容，优先级为：

1. 请求体中的 `lang` 字段（BCP 47 标签，如 `en`、`zh-Hans`）
2. `Accept-Language` 请求头
3. 服务端默认值 `AGENT_DEFAULT_LANG`（默认 `zh-Hans`）

该语言决定 Agent 使用的 Prompt 文本、模型读到的工具描述、步骤摘要以及错误信息的语言。
工具名、JSON 字段名、`action` 取值与 `[工具 X 返回]` 标记都是协议常量，不随语言变化。

## 认证

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/auth/register` | `{username, password}` → `201` |
| POST | `/auth/login` | `{username, password}` → `{token, user_id, username}` |
| GET | `/auth/me` | → `{id, username, created_at}` |

## 笔记

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/notes?search=` | 笔记列表，`search` 匹配标题 |
| POST | `/notes` | `{title, content}` → `201`，创建时即建立索引 |
| GET | `/notes/{id}` | 单篇笔记 |
| PUT | `/notes/{id}` | `{title?, content?}`，自动重建索引 |
| DELETE | `/notes/{id}` | 删除笔记及其向量 |
| POST | `/notes/{id}/reindex` | 重建单篇笔记的索引 |

笔记字段：`id`（UUID）、`title`、`content`、`source_type`（`manual` / `pdf` / `pptx` / `markdown`）、`source_name`、`created_at`、`updated_at`。

## Agent

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/agent/sessions` | `{goal}` → `201`，返回 `{session_id, summary, plan, steps, eval, weak_points, conversation}` |
| POST | `/agent/sessions/{id}/chat` | `{message}` → `{session_id, reply, conversation}` |
| POST | `/agent/sessions/{id}/answers` | 提交答题结果，见下文 |
| GET | `/agent/sessions` | 会话列表 |
| GET | `/agent/sessions/{id}` | 会话详情，含完整对话 |
| GET | `/agent/sessions/{id}/eval` | 评测报告 `{metrics, details}` |

`{goal}` 与 `{message}` 都接受可选的 `lang` 字段，用于单独覆盖本次请求的语言。

创建会话会完整跑一遍 ReAct 循环，直到助手给出最终回答才返回，因此该请求耗时较长。用 `/chat` 继续会话时，会在同一段对话上再跑一轮循环。

`steps` 的每一项都带有 `success`，工具调用失败时还带 `error`。判断成败请读这两个字段，不要去解析 `summary`——它的措辞随请求语言变化。

### 评测指标

| 指标 | 定义 |
|---|---|
| `task_completion_rate` | 已完成步骤 / 计划步骤 |
| `tool_call_success_rate` | 成功工具调用 / 工具调用总数 |
| `avg_latency_ms` | 每次工具调用的平均耗时 |
| `plan_deviation_rate` | 实际使用的工具集与计划工具集的偏离程度 |

### 答题闭环

提交答题结果会更新相关笔记的长期记忆。这是整个复习闭环的收口：下一次会话会从更新后的掌握度和新的薄弱点列表开始。

请求：

```json
{"answers": [{"question": "...", "selected": "A. ...", "correct": "A. ...", "is_correct": true}]}
```

响应：`{"session_id", "correct", "total", "mastery_level", "weak_points"}`

## 文件上传

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/upload` | `multipart/form-data`，字段名 `file`（`.pdf`、`.pptx`、`.md`）→ `201` `{note_id, title}` |

文件在一次请求中完成解析、分块、向量化并保存为笔记。

## 工具清单

以下是助手可调用的工具。模型会读取它们的描述与参数结构，每轮选择其中一个。

| 工具 | 用途 | 参数 |
|---|---|---|
| `search_notes` | 跨笔记向量检索 | `query` |
| `generate_summary` | 摘要、关键概念与复习重点 | `note_ids` |
| `create_quiz` | 生成选择题 | `note_ids`、`count` |
| `cross_reference` | 两篇笔记之间的关联 | `note_id` |
| `explain_concept` | 用通俗语言解释概念 | `concept` |

## 配置

所有配置从 `backend/.env` 读取，带注释的完整清单见 `backend/.env.example`。

| 变量 | 说明 |
|---|---|
| `LLM_MODEL` | 模型注册表的键，选择使用的模型 |
| `LLM_PROVIDER` | 未设置 `LLM_MODEL` 时生效的旧式兜底项 |
| `MODELSCOPE_API_KEY`、`MOONSHOT_API_KEY`、`NVIDIA_API_KEY` | 各 provider 的凭据 |
| `LLM_MIN_INTERVAL` | 全局最小调用间隔（秒）；`0` 表示使用各模型自身的间隔 |
| `MAX_STEPS`、`LLM_TEMPERATURE`、`TOOL_OUTPUT_MAX_CHARS`、`SESSION_TIMEOUT_SECONDS` | Agent 循环限制 |
| `JWT_SECRET`、`JWT_EXPIRE_MINUTES` | 令牌签名与有效期 |
| `EMBEDDING_MODEL`、`CHUNK_SIZE`、`CHUNK_OVERLAP` | 检索相关设置 |
| `DATABASE_PATH`、`CHROMA_PATH` | 可选的存储路径覆盖 |
