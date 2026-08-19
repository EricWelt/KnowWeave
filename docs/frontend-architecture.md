# KnowWeave 前端架构文档（）

> 版本：v2.0 | 配套后端：FastAPI + ReAct Agent（见 docs/api.md）

## 1. 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| UI | Flutter + Material 3 | 三端一致（Android/iOS/Web），MD3 原生支持 |
| 状态管理 | flutter_riverpod 2.x | 编译期安全、可测试、可注入（替代裸 setState） |
| 路由 | go_router 14.x | 声明式路由 + auth 重定向 + 深链 |
| 网络 | http + 自研 ApiClient | 轻量；注入 http.Client 便于 mock 测试 |
| 存储 | shared_preferences | JWT / 主题模式持久化 |
| 动画 | 系统动画 + 玻璃质感点缀 | 见「视觉规范」 |
| 文件 | file_picker | PDF/PPTX/MD 导入 |

## 2. 目录结构

```
lib/
├── main.dart                    # 入口：ProviderScope + MaterialApp.router + 主题模式
├── core/                        # 与业务无关的基础设施
│   ├── config/app_config.dart   # --dart-define 可覆盖的后端地址
│   ├── network/
│   │   ├── api_client.dart      # 统一 HTTP：Bearer/UTF-8/错误映射（可注入）
│   │   └── api_exception.dart   # 带 statusCode 的统一异常
│   ├── storage/token_store.dart # JWT + 用户信息
│   ├── router/app_router.dart   # go_router：底栏三页 Shell + auth 重定向
│   ├── widgets/shell_screen.dart  # 底栏外壳（笔记/AI 助手/我的）
│   ├── theme/app_theme.dart     # MD3 亮/暗主题 + 组件主题 + 转场
│   ├── widgets/
│   │   ├── glass.dart           # 玻璃质感组件（性能安全的小面积模糊）
│   │   ├── markdown_view.dart   # 全 App 唯一 Markdown+LaTeX 渲染
│   │   └── status_views.dart    # Loading/Empty/Error 统一组件
│   └── providers.dart           # prefs / tokenStore / apiClient 全局注入点
├── features/                    # 按业务域分模块（高内聚）
│   ├── auth/                    # 认证
│   │   ├── auth_repository.dart # 登录/注册（调 ApiClient）
│   │   ├── auth_provider.dart   # AuthState + 登录/登出/自动恢复
│   │   └── screens/             # login / register
│   ├── notes/                   # 笔记
│   │   ├── note_model.dart      # Note（与后端 NoteOut 对齐）
│   │   ├── note_repository.dart # CRUD + reindex + upload
│   │   ├── note_provider.dart   # AsyncNotifier 列表状态
│   │   └── screens/             # list / edit
│   └── agent/                   # AI 助手
│       ├── models/agent_models.dart  # 会话/步骤/评测/题目/作答 模型
│       ├── agent_repository.dart     # /agent/* + /answers
│       ├── agent_provider.dart       # 对话状态机 + 题目提取（修复版）
│       └── screens/
│           ├── agent_chat_screen.dart
│           └── widgets/
│               ├── chat_bubble.dart  # 气泡/工具卡/题目卡/结果卡
│               └── quiz_card.dart    # 可交互选择题 + 作答上报
└── test/
    ├── unit/       # 纯逻辑（题目提取等）
    └── widget/     # MockClient 注入的 UI 流程测试

> 新增：features/profile/（「我的」页：账号/外观/退出）
```

## 3. 依赖注入与可测试性（核心设计）

**规则：任何 IO（HTTP/存储）都通过可注入抽象，测试用替身替换。**

```dart
// core/providers.dart —— 全局注入点
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient(
  client: http.Client(),                      // ← 测试改为 MockClient
  tokenStore: ref.watch(tokenStoreProvider),
));

// 测试：override 注入假客户端
apiClientProvider.overrideWithValue(
  ApiClient(client: MockClient(...), tokenStore: ..., baseUrl: 'http://test'),
);
```

分层调用链：`Screen → Provider(状态) → Repository(数据) → ApiClient(HTTP)`。
每层只依赖下层接口 → 每层都可单独测试。

## 3.5 底栏三页（Shell）与页面职责

- **笔记**：列表 + 导入（顶栏仅保留导入按钮）
- **AI 助手**：对话 + 思考过程展示 + 历史会话（独立底栏页）
- **我的**：账号信息 + 外观（亮/暗/跟随系统）+ 退出登录

跨页上下文（笔记 → AI）：`agentDraftGoalProvider` 携带「围绕笔记《X》帮我复习」草稿目标，
切到 AI 页自动消费发送。

## 4. 状态管理约定

- **全局状态**（登录态、主题模式）用 `Notifier`；
- **异步数据**（笔记列表）用 `AsyncNotifier`（自带 loading/error/data 三态）；
- **对话状态机**用 `Notifier`（消息列表 + sessionId + loading）；
- 页面内局部 UI 状态（输入框、预览开关）保留 `setState`。

## 5. 视觉规范（MD3 + 玻璃点缀）

### 5.1 配色
- 品牌种子色 `teal #00897B`，`ColorScheme.fromSeed` 生成全套；
- 亮/暗两套 `ThemeData`，`themeMode` 持久化（system/light/dark）；
- 组件级主题统一：AppBar 半透明、卡片圆角 16、输入框填充式、按钮圆角 14。

### 5.2 玻璃质感（克制原则）
- 只在 **AppBar 背景 / 登录注册卡片** 使用 `BackdropFilter`；
- 双层效果：半透明底色 + 1px 白色高光描边；
- `Glass.enabled = false` 可全局关闭（低端机兜底）。

### 5.3 动效
- 页面转场：MD3 fade-through（`FadeForwardsPageTransitionsBuilder`）；
- 聊天气泡、列表项进出场动画；
- 主题切换动画（MaterialApp 内置）；
- AI 思考中：三个错相脉动的圆点 + 「AI 思考中…」（`ThinkingIndicator`）；
- 思考过程：回答附带可折叠的「思考过程」卡片（think 文本 + 工具调用），类似 LLM 深度思考展示。

## 6. 后端契约速查

| 前端调用 | 端点 |
|---|---|
| 登录/注册 | POST /auth/login、/auth/register |
| 笔记列表/详情/增删改/重建索引 | GET/POST /notes、GET/PUT/DELETE /notes/{id}、POST /notes/{id}/reindex |
| 导入 | POST /upload (multipart) |
| 发起/继续 Agent 会话 | POST /agent/sessions、/agent/sessions/{id}/chat |
| 会话列表/详情/评测 | GET /agent/sessions、/{id}、/{id}/eval |
| **答题闭环** | **POST /agent/sessions/{id}/answers** |

完整字段见 `docs/api.md`。

## 7. 真机联调

1. PC 与手机同一 WiFi；
2. 后端：`uvicorn backend.main:app --host 0.0.0.0 --port 8000`；
3. 前端：`flutter build apk --dart-define=API_BASE_URL=http://<PC局域网IP>:8000`；
4. Android release 已配置 INTERNET 权限 + cleartext（manifest）；iOS 已配置 ATS NSAllowsLocalNetworking。

## 8. 已知取舍与后续 TODO

- [ ] 登录后自动刷新笔记（当前页面进入时加载）
- [ ] Agent 流式输出（SSE）
- [ ] 文件导入的 Web 端（file_picker web 需 bytes 处理）
- [ ] 会话消息虚拟化（长对话性能）