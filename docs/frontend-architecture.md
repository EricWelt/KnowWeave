English丨[简体中文](frontend-architecture.zh-Hans.md)

# KnowWeave App Architecture

> Version 2.0 · Talks to the FastAPI backend and ReAct agent described in [api.md](api.md).

## 1. Stack

| Layer | Choice | Why |
|---|---|---|
| UI | Flutter with Material 3 | One codebase for Android, iOS, and web, with first-class Material 3 support |
| State | flutter_riverpod 2.x | Compile-time safe, testable, injectable; replaces ad-hoc `setState` |
| Routing | go_router 14.x | Declarative routes, auth redirects, deep links |
| Network | `http` behind a small `ApiClient` | Lightweight, and the underlying `http.Client` can be swapped for a mock in tests |
| Storage | shared_preferences | Persists the JWT and the theme mode |
| Files | file_picker | Imports PDF, PPTX, and Markdown |
| Localization | flutter_localizations with gen-l10n and ARB resources | Official tooling; English and Simplified Chinese |

## 2. Layout

```
lib/
├── main.dart                    # Entry point: ProviderScope, MaterialApp.router, theme mode
├── core/                        # Infrastructure, no business logic
│   ├── config/app_config.dart   # Backend URL, overridable with --dart-define
│   ├── l10n/l10n.dart           # AppLanguage enum and the context.l10n shorthand
│   ├── network/
│   │   ├── api_client.dart      # Bearer token, UTF-8 decoding, error mapping
│   │   └── api_exception.dart   # One exception type carrying the status code
│   ├── storage/token_store.dart # JWT and the signed-in user
│   ├── router/app_router.dart   # go_router: three-tab shell plus auth redirects
│   ├── theme/app_theme.dart     # Material 3 light and dark themes, component themes, transitions
│   ├── widgets/
│   │   ├── shell_screen.dart    # Bottom navigation shell (notes, assistant, profile)
│   │   ├── glass.dart           # Frosted-glass surfaces, blurred in small areas only
│   │   ├── markdown_view.dart   # The single Markdown and LaTeX renderer
│   │   └── status_views.dart    # Shared loading, empty, and error views
│   └── providers.dart           # Where prefs, token store, and API client are injected
├── features/                    # One folder per business domain
│   ├── auth/
│   │   ├── auth_repository.dart # Login and registration calls
│   │   ├── auth_provider.dart   # Auth state, sign-in, sign-out, session restore
│   │   └── screens/             # login, register
│   ├── notes/
│   │   ├── note_model.dart      # Note, mirroring the backend schema
│   │   ├── note_repository.dart # CRUD, reindex, upload
│   │   ├── note_provider.dart   # AsyncNotifier holding the list state
│   │   └── screens/             # list, edit
│   ├── agent/
│   │   ├── models/agent_models.dart  # Session, step, evaluation, quiz, and answer models
│   │   ├── agent_repository.dart     # /agent/* and /answers
│   │   ├── agent_provider.dart       # Conversation state machine and quiz extraction
│   │   └── screens/
│   │       ├── agent_chat_screen.dart
│   │       └── widgets/
│   │           ├── chat_bubble.dart  # Bubbles, tool cards, quiz cards, result cards
│   │           └── quiz_card.dart    # Interactive questions that report answers back
│   └── profile/                      # Account, appearance, language, sign-out
├── l10n/                             # ARB resources and generated lookups
│   ├── app_en.arb
│   ├── app_zh.arb                    # base locale, required by gen-l10n
│   └── app_zh_Hans.arb               # Simplified Chinese
└── test/
    ├── unit/       # Pure logic
    └── widget/     # UI flows with a mocked HTTP client
```

## 3. Dependency Injection and Testability

The rule is that any I/O, whether HTTP or storage, goes through an injectable abstraction, and tests substitute a stand-in.

```dart
// core/providers.dart
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient(
  client: http.Client(),                      // replaced with MockClient in tests
  tokenStore: ref.watch(tokenStoreProvider),
));

// in a test
apiClientProvider.overrideWithValue(
  ApiClient(client: MockClient(...), tokenStore: ..., baseUrl: 'http://test'),
);
```

Calls flow screen → provider (state) → repository (data) → `ApiClient` (HTTP). Each layer depends only on the one below it, so each can be tested on its own.

## 4. The Three Tabs

- **Notes**: the list plus import; the app bar keeps only the import action.
- **Assistant**: the conversation, the reasoning trace, and past sessions, on its own tab.
- **Profile**: account information, appearance (light, dark, or system), interface language, and sign-out.

Cross-tab context: opening the assistant from a note seeds `agentDraftGoalProvider` with a goal such as "help me revise <note title>", which the chat screen consumes and sends automatically.

## 5. State Management Conventions

- Global state such as the signed-in user, the theme mode, and the interface language uses a `Notifier`.
- Asynchronous data such as the note list uses an `AsyncNotifier`, which carries loading, error, and data states.
- The conversation uses a `Notifier` holding the message list, the session id, and a loading flag.
- Purely local UI state, such as a text field or a preview toggle, stays with `setState`.

## 6. Visual Language

### 6.1 Color

- The seed color is teal `#00897B`; `ColorScheme.fromSeed` derives the full palette.
- Separate light and dark `ThemeData`; the mode is persisted as system, light, or dark.
- Component themes are set centrally: a translucent app bar, cards with a 16 radius, filled text fields, and buttons with a 14 radius.

### 6.2 Frosted glass, used sparingly

- `BackdropFilter` appears only on the app bar and the sign-in cards.
- The effect is a translucent fill plus a one-pixel light stroke.
- `Glass.enabled = false` turns it off globally for slower devices.

### 6.3 Motion

- Page transitions use the Material 3 fade-through builder.
- Chat bubbles and list items animate in and out.
- The thinking indicator is three pulsing dots with an "assistant is thinking" label.
- Finished answers can expand a collapsed reasoning card showing the model's thoughts and the tool calls of that turn.

## 7. Backend Contract

| What the app calls | Endpoint |
|---|---|
| Sign in and register | `POST /auth/login`, `POST /auth/register` |
| Note list, detail, create, update, delete, reindex | `GET/POST /notes`, `GET/PUT/DELETE /notes/{id}`, `POST /notes/{id}/reindex` |
| Import | `POST /upload` (multipart) |
| Start and continue a session | `POST /agent/sessions`, `POST /agent/sessions/{id}/chat` |
| Session list, detail, evaluation | `GET /agent/sessions`, `/agent/sessions/{id}`, `/agent/sessions/{id}/eval` |
| Quiz answers | `POST /agent/sessions/{id}/answers` |

Field-level detail lives in [api.md](api.md).

## 8. Running Against a Device

1. Put the computer and the phone on the same network.
2. Start the backend: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
3. Build the app with the computer's address: `flutter build apk --dart-define=API_BASE_URL=http://<host>:8000`.
4. Android release builds declare the INTERNET permission and allow cleartext traffic; iOS declares an ATS local networking exception.

## 9. Known Trade-offs and Open Work

- [ ] Refresh the note list after sign-in; today it loads when the screen opens.
- [ ] Stream assistant replies with SSE.
- [ ] File import on the web, which needs byte handling in file_picker.
- [ ] Virtualize long conversations.
