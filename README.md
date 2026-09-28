English丨[简体中文](README.zh-Hans.md)

<div align="center">
  <h1>KnowWeave</h1>
  <p>Keep your study notes in Markdown, and let an AI assistant read them, summarize them, quiz you, and explain what you missed.</p>
  <p>
    <a href="#quick-start"><strong>Get Started</strong></a>
    ·
    <a href="docs/api.md"><strong>API Reference</strong></a>
    ·
    <a href="docs/frontend-architecture.md"><strong>Architecture</strong></a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
    <img src="https://img.shields.io/badge/python-3.10%2B-3776ab.svg" alt="Python 3.10 or later">
    <img src="https://img.shields.io/badge/flutter-Material%203-02569b.svg" alt="Flutter with Material 3">
  </p>
</div>

KnowWeave is a note-taking app for studying. You write notes in Markdown, optionally import PDF, PowerPoint, or Markdown files, and then work with an assistant that reasons over what you have written.

The assistant runs a ReAct loop: it plans a few steps, calls one tool at a time, reads the result, and keeps going until it can answer. It can search your notes by meaning, write a summary, generate a multiple-choice quiz, explain a concept you keep getting wrong, and point out how two notes relate. Every step it takes is recorded, so you can inspect which tools ran, how long each one took, and where the run drifted from its original plan.

## Features

**Study assistant**

- A ReAct (Reasoning and Acting) loop written for this project. No agent framework is involved; the model's decisions are plain JSON, so any OpenAI-compatible endpoint can drive it.
- Five tools: `search_notes`, `generate_summary`, `create_quiz`, `cross_reference`, and `explain_concept`. They are declared in one registry, which also produces the descriptions the model reads when choosing a tool.
- Quiz results feed back into a mastery level per note, together with the weak points worth revisiting.

**Memory**

- Short term: the recent turns of the current conversation.
- Long term: mastery level and weak points per note, stored in SQLite and updated after each quiz.
- Semantic: note chunks embedded locally and retrieved by vector similarity.

**Retrieval**

- One upload endpoint accepts PDF, PowerPoint, and Markdown files; text notes are indexed as you create them.
- Documents are parsed, split into overlapping chunks, embedded with BGE (`BAAI/bge-small-zh-v1.5`), and stored in ChromaDB. Embeddings run locally, so no external service is required.

**Evaluation**

- Each step records its duration and outcome.
- A session aggregates into task completion rate, tool call success rate, average tool latency, and plan deviation rate.

**Models**

- A registry of OpenAI-compatible providers, switched with a single environment variable. ModelScope, NVIDIA build, and Moonshot are configured out of the box, and adding another endpoint is a small edit to one dictionary.

## Quick Start

### Backend

```bash
# Install dependencies (Python 3.10 or later)
pip install -r backend/requirements.txt

# Create your configuration and fill in the API key for one provider
cp backend/.env.example backend/.env

# Start the API. Swagger UI is served at http://127.0.0.1:8000/docs
uvicorn backend.main:app --reload --port 8000
```

### App

```bash
cd app
flutter pub get
flutter run

# Point a release build at your backend
flutter build apk --dart-define=API_BASE_URL=http://<your-host>:8000
```

The interface follows the system language and can be switched between English and Simplified Chinese from the profile tab. The assistant answers in the same language, from its prompts down to its error messages.

## How It Works

A request such as "help me revise chapter three of my operating systems notes" runs through four stages.

1. The planner turns the goal into an ordered list of steps. The plan is advisory: the agent may deviate, and the deviation rate is measured.
2. The ReAct loop asks the model for one decision per turn in JSON: what it is thinking, which tool to call, and with which parameters. The engine runs that tool, appends the observation to the conversation, and asks again.
3. Tools chain naturally. `search_notes` finds the relevant notes, `generate_summary` builds an overview, `create_quiz` produces questions, and `explain_concept` covers whatever the quiz exposed.
4. Results are written back: mastery levels and weak points are updated, and the evaluation record for the session is stored.

The loop is bounded. A session runs at most 15 steps, tool output is truncated to 2000 characters before it enters the context, sessions idle for more than 300 seconds are marked abandoned, and a failing tool call is returned to the model as an observation rather than crashing the run.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), SQLite in WAL mode |
| Agent | ReAct loop, tool registry, three-layer memory, evaluation tracking |
| Retrieval | ChromaDB, BGE-small-zh-v1.5 embeddings, overlapping chunker |
| Models | Any OpenAI-compatible endpoint |
| App | Flutter, Riverpod, go_router, Material 3 |

## Documentation

| Document | Description |
|---|---|
| [docs/api.md](docs/api.md) | Endpoints, payloads, and evaluation metrics |
| [docs/frontend-architecture.md](docs/frontend-architecture.md) | App layering, dependency injection, theming, and the notes-to-assistant flow |

## Configuration

Settings live in `backend/.env`; `backend/.env.example` lists all of them with comments.

| Variable | Description |
|---|---|
| `LLM_MODEL` | Which entry of the model registry to use |
| `MODELSCOPE_API_KEY`, `MOONSHOT_API_KEY`, `NVIDIA_API_KEY` | Credentials for the provider you choose; fill in one |
| `LLM_MIN_INTERVAL` | Minimum seconds between calls, a global override for providers with tight rate limits |
| `MAX_STEPS` | Step ceiling for one session (default 15) |
| `LLM_TEMPERATURE` | Sampling temperature (default 0.3) |
| `JWT_SECRET` | Signing key for access tokens; change it before exposing the API |
| `EMBEDDING_MODEL` | Local embedding model (default `BAAI/bge-small-zh-v1.5`) |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Document chunking parameters |

## Contributing

1. Fork the repository and create a branch: `git checkout -b feat/short-description`.
2. Keep commits to [Conventional Commits](https://www.conventionalcommits.org/), one logical change per commit.
3. Run the test suites before opening a pull request:

```bash
cd backend && pytest
cd app && flutter test
```

4. Open the pull request and describe what changed and how you verified it.

## License

MIT. See [LICENSE](LICENSE).
