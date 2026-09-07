[English](frontend-architecture.md)丨简体中文

# KnowWeave 前端架构文档

> 版本 2.0 · 对接的后端见 [api.zh-Hans.md](api.zh-Hans.md)（FastAPI + ReAct Agent）。

## 1. 技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| UI | Flutter + Material 3 | 一套代码覆盖 Android/iOS/Web，MD3 原生支持 |
| 状态管理 | flutter_riverpod 2.x | 编译期安全、可测试、可注入，替代零散的 `setState` |
| 路由 | go_router 14.x | 声明式路由、登录重定向、深链 |
| 网络 | `http` + 自研 `ApiClient` | 轻量；底层 `http.Client` 可在测试中替换为 mock |
| 存储 | shared_preferences | 持久化 JWT 与主题模式 |
| 文件 | file_picker | 导入 PDF、PPTX、Markdown |

## 2. 目录结构

```
lib/
├── main.dart                    # 入口：ProviderScope、MaterialApp.router、主题模式
├── core/                        # 基础设施，不含业务逻辑
│   ├── config/app_config.dart   # 后端地址，可用 --dart-define 覆盖
│   ├── network/
│   │   ├── api_client.dart      # Bearer 令牌、UTF-8 解码、错误映射
│   │   └── api_exception.dart   # 统一异常类型，携带状态码
│   ├── storage/token_store.dart # JWT 与登录用户信息
│   ├── router/app_router.dart   # go_router：底栏三页外壳 + 登录重定向
│   ├── theme/app_theme.dart     # Material 3 亮/暗主题、组件主题、转场
│   ├── widgets/
│   │   ├── shell_screen.dart    # 底栏外壳（笔记 / AI 助手 / 我的）
│   │   ├── glass.dart           # 玻璃质感组件，仅小面积模糊
│   │   ├── markdown_view.dart   # 全 App 唯一的 Markdown 与 LaTeX 渲染器
│   │   └── status_views.dart    # 统一的加载 / 空 / 错误视图
│   └── providers.dart           # prefs、tokenStore、apiClient 的注入点
├── features/                    # 按业务域分目录
│   ├── auth/
│   │   ├── auth_repository.dart # 登录、注册调用
│   │   ├── auth_provider.dart   # 登录态、登录、登出、会话恢复
│   │   └── screens/             # login、register
│   ├── notes/
│   │   ├── note_model.dart      # Note，与后端 schema 对齐
│   │   ├── note_repository.dart # 增删改查、重建索引、上传
│   │   ├── note_provider.dart   # AsyncNotifier 维护列表状态
│   │   └── screens/             # list、edit
│   ├── agent/
│   │   ├── models/agent_models.dart  # 会话、步骤、评测、题目、作答模型
│   │   ├── agent_repository.dart     # /agent/* 与 /answers
│   │   ├── agent_provider.dart       # 对话状态机与题目提取
│   │   └── screens/
│   │       ├── agent_chat_screen.dart
│   │       └── widgets/
│   │           ├── chat_bubble.dart  # 气泡、工具卡、题目卡、结果卡
│   │           └── quiz_card.dart    # 可交互题目，作答后回传
│   └── profile/                      # 账号、外观、退出登录
└── test/
    ├── unit/       # 纯逻辑
    └── widget/     # 注入 mock HTTP 客户端的界面流程测试
```

## 3. 依赖注入与可测试性

约定：任何 IO（HTTP 或存储）都经过可注入的抽象，测试时替换为替身。

```dart
// core/providers.dart
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient(
  client: http.Client(),                      // 测试中替换为 MockClient
  tokenStore: ref.watch(tokenStoreProvider),
));

// 测试中
apiClientProvider.overrideWithValue(
  ApiClient(client: MockClient(...), tokenStore: ..., baseUrl: 'http://test'),
);
```

调用链为「页面 → Provider（状态）→ Repository（数据）→ ApiClient（HTTP）」。每层只依赖下一层的接口，因此可以单独测试。

## 4. 底栏三页

- **笔记**：列表与导入，顶栏只保留导入按钮。
- **AI 助手**：对话、思考过程展示、历史会话，独立占一个底栏页。
- **我的**：账号信息、外观（亮色/暗色/跟随系统）、退出登录。

跨页上下文：从笔记页唤起助手时，`agentDraftGoalProvider` 会带上「围绕《笔记标题》帮我复习」这样的目标，对话页消费后自动发送。

## 5. 状态管理约定

- 全局状态（登录态、主题模式）用 `Notifier`。
- 异步数据（笔记列表）用 `AsyncNotifier`，自带 loading / error / data 三态。
- 对话状态机用 `Notifier`，持有消息列表、sessionId 与加载标志。
- 纯局部 UI 状态（输入框内容、预览开关）保留 `setState`。

## 6. 视觉规范

### 6.1 配色

- 种子色为 teal `#00897B`，由 `ColorScheme.fromSeed` 推导整套配色。
- 亮/暗两套 `ThemeData`，模式持久化为跟随系统、亮色或暗色。
- 组件主题集中设置：AppBar 半透明、卡片圆角 16、输入框填充式、按钮圆角 14。

### 6.2 玻璃质感（克制使用）

- `BackdropFilter` 仅出现在 AppBar 与登录/注册卡片上。
- 效果为半透明底色加 1 像素白色高光描边。
- `Glass.enabled = false` 可全局关闭，供低端设备兜底。

### 6.3 动效

- 页面转场使用 Material 3 的 fade-through 转场。
- 聊天气泡与列表项带进出场动画。
- 思考指示器是三个错相脉动的圆点，配「助手思考中」文案。
- 回答完成后可展开折叠的思考卡片，查看模型当时的思考与工具调用。

## 7. 后端契约速查

| 前端调用 | 端点 |
|---|---|
| 登录与注册 | `POST /auth/login`、`POST /auth/register` |
| 笔记列表、详情、增删改、重建索引 | `GET/POST /notes`、`GET/PUT/DELETE /notes/{id}`、`POST /notes/{id}/reindex` |
| 导入 | `POST /upload`（multipart） |
| 发起与继续会话 | `POST /agent/sessions`、`POST /agent/sessions/{id}/chat` |
| 会话列表、详情、评测 | `GET /agent/sessions`、`/agent/sessions/{id}`、`/agent/sessions/{id}/eval` |
| 答题闭环 | `POST /agent/sessions/{id}/answers` |

字段级细节见 [api.zh-Hans.md](api.zh-Hans.md)。

## 8. 真机联调

1. 电脑与手机连同一网络。
2. 启动后端：`uvicorn backend.main:app --host 0.0.0.0 --port 8000`。
3. 带上电脑地址构建客户端：`flutter build apk --dart-define=API_BASE_URL=http://<主机地址>:8000`。
4. Android release 已声明 INTERNET 权限并允许明文流量；iOS 已声明 ATS 本地网络例外。

## 9. 已知取舍与待办

- [ ] 登录后自动刷新笔记列表，目前为进入页面时加载。
- [ ] 助手回复流式输出（SSE）。
- [ ] Web 端文件导入，需要在 file_picker 中处理字节流。
- [ ] 长会话的消息虚拟化。
