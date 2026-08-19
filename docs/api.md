# KnowWeave 后端 API 文档

> 基础地址：`http://localhost:8000`（Swagger: /docs）
> 认证：除 `/auth/register`、`/auth/login` 外，均需请求头 `Authorization: Bearer <token>`

## 认证 /auth

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /auth/register | {`username`, `password`} → 201 |
| POST | /auth/login | {`username`, `password`} → {`token`, `user_id`, `username`} |
| GET | /auth/me | → {`id`, `username`, `created_at`} |

## 笔记 /notes

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /notes?search= | 笔记列表（标题模糊搜索） |
| POST | /notes | {`title`, `content`} → 201（自动向量化） |
| GET | /notes/{id} | 笔记详情 |
| PUT | /notes/{id} | {`title?`, `content?`}（自动重建索引） |
| DELETE | /notes/{id} | 删除（含向量清理） |
| POST | /notes/{id}/reindex | 手动重建索引 |

笔记字段：`id`(UUID) `title` `content` `source_type`(manual/pdf/pptx/markdown) `source_name` `created_at` `updated_at`

## Agent /agent

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /agent/sessions | {`goal`} → 201 {`session_id`, `summary`, `plan`, `steps`, `eval`, `weak_points`, `conversation`} |
| POST | /agent/sessions/{id}/chat | {`message`} → {`session_id`, `reply`, `conversation`} |
| GET | /agent/sessions | 会话列表 |
| GET | /agent/sessions/{id} | 会话详情（含完整对话） |
| GET | /agent/sessions/{id}/eval | 评测报告 {`metrics`, `details`} |

### eval 指标
- `task_completion_rate`：完成步骤/计划步骤
- `tool_call_success_rate`：成功工具调用/总调用
- `avg_latency_ms`：工具平均耗时
- `plan_deviation_rate`：实际工具集与计划工具集的偏差

## 文件上传 /upload

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /upload | multipart `file`（pdf/pptx/md）→ 201 {`note_id`, `title`} |


| POST | /agent/sessions/{id}/answers | 提交选择题作答 → 更新知识掌握状态 |

### 答题闭环 /answers

请求：
```json
{"answers": [{"question": "...", "selected": "A. x", "correct": "A. x", "is_correct": true}]}
```
响应：{"session_id", "correct", "total", "mastery_level", "weak_points"}

## Agent 工具清单

| 工具 | 用途 | 关键参数 |
|---|---|---|
| search_notes | 向量检索笔记 | query |
| generate_summary | 摘要+关键概念+复习重点 | note_ids |
| create_quiz | 生成选择题 | note_ids, count |
| cross_reference | 跨笔记关联 | note_id |
| explain_concept | 费曼解释概念 | concept |

## 配置（.env）

`LLM_PROVIDER`（modelscope|moonshot）、`MODELSCOPE_API_KEY`、`MOONSHOT_API_KEY`、
`MODELSCOPE_MODEL`、`MOONSHOT_MODEL`、`MAX_STEPS`、`LLM_TEMPERATURE`、
`JWT_SECRET`、`EMBEDDING_MODEL`、`CHUNK_SIZE` 等，详见 `backend/.env.example`。