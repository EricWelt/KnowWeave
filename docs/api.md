English丨[简体中文](api.zh-Hans.md)

# KnowWeave API Reference

> Base URL: `http://localhost:8000` · Interactive docs: `/docs`
> Authentication: every endpoint except `/auth/register` and `/auth/login` requires the header `Authorization: Bearer <token>`.

## Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | `{username, password}` → `201` |
| POST | `/auth/login` | `{username, password}` → `{token, user_id, username}` |
| GET | `/auth/me` | → `{id, username, created_at}` |

## Notes

| Method | Path | Description |
|---|---|---|
| GET | `/notes?search=` | List notes; `search` matches the title |
| POST | `/notes` | `{title, content}` → `201`, indexed on creation |
| GET | `/notes/{id}` | One note |
| PUT | `/notes/{id}` | `{title?, content?}`, reindexes automatically |
| DELETE | `/notes/{id}` | Deletes the note and its vectors |
| POST | `/notes/{id}/reindex` | Rebuilds the index for one note |

A note has the fields `id` (UUID), `title`, `content`, `source_type` (`manual` / `pdf` / `pptx` / `markdown`), `source_name`, `created_at`, and `updated_at`.

## Agent

| Method | Path | Description |
|---|---|---|
| POST | `/agent/sessions` | `{goal}` → `201` with `{session_id, summary, plan, steps, eval, weak_points, conversation}` |
| POST | `/agent/sessions/{id}/chat` | `{message}` → `{session_id, reply, conversation}` |
| POST | `/agent/sessions/{id}/answers` | Quiz answers, see below |
| GET | `/agent/sessions` | Session list |
| GET | `/agent/sessions/{id}` | One session, including the full conversation |
| GET | `/agent/sessions/{id}/eval` | Evaluation report `{metrics, details}` |

Creating a session runs the full ReAct loop and returns once the agent has produced its final answer, so this call can take a while. Continuing a session with `/chat` runs another loop over the same conversation.

### Evaluation metrics

| Metric | Definition |
|---|---|
| `task_completion_rate` | Steps completed over steps planned |
| `tool_call_success_rate` | Successful tool calls over total tool calls |
| `avg_latency_ms` | Mean wall-clock time per tool call |
| `plan_deviation_rate` | Distance between the tools actually used and the tools the plan named |

### Quiz answers

Submitting answers updates the long-term memory for the notes involved. This is what closes the study loop: the next session starts from an updated mastery level and a fresh list of weak points.

Request:

```json
{"answers": [{"question": "...", "selected": "A. ...", "correct": "A. ...", "is_correct": true}]}
```

Response: `{"session_id", "correct", "total", "mastery_level", "weak_points"}`

## File upload

| Method | Path | Description |
|---|---|---|
| POST | `/upload` | `multipart/form-data` with a `file` field (`.pdf`, `.pptx`, `.md`) → `201` `{note_id, title}` |

The file is parsed, chunked, embedded, and stored as a note in one request.

## Tools

These are the tools the agent can call. The model sees the descriptions and parameter schemas, and picks one per turn.

| Tool | Purpose | Parameters |
|---|---|---|
| `search_notes` | Vector search across notes | `query` |
| `generate_summary` | Summary, key concepts, and review points | `note_ids` |
| `create_quiz` | Multiple-choice questions | `note_ids`, `count` |
| `cross_reference` | Relationship between two notes | `note_id` |
| `explain_concept` | Plain-language explanation of a concept | `concept` |

## Configuration

All settings are read from `backend/.env`; see `backend/.env.example` for the annotated list.

| Variable | Description |
|---|---|
| `LLM_MODEL` | Registry key selecting the model to use |
| `LLM_PROVIDER` | Legacy fallback used when `LLM_MODEL` is unset |
| `MODELSCOPE_API_KEY`, `MOONSHOT_API_KEY`, `NVIDIA_API_KEY` | Provider credentials |
| `LLM_MIN_INTERVAL` | Global minimum interval between calls, in seconds; `0` uses each model's own interval |
| `MAX_STEPS`, `LLM_TEMPERATURE`, `TOOL_OUTPUT_MAX_CHARS`, `SESSION_TIMEOUT_SECONDS` | Agent loop limits |
| `JWT_SECRET`, `JWT_EXPIRE_MINUTES` | Token signing and lifetime |
| `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP` | Retrieval settings |
| `DATABASE_PATH`, `CHROMA_PATH` | Optional storage overrides |
