import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:know_weave/core/network/api_client.dart';
import 'package:know_weave/core/providers.dart';
import 'package:know_weave/core/storage/token_store.dart';
import 'package:know_weave/features/agent/agent_provider.dart';
import 'package:know_weave/main.dart';

/// 构建被测应用。language 为 null 表示不写入偏好（即跟随系统）。
Future<Widget> buildTestApp({required http.Client client, String? language}) async {
  SharedPreferences.setMockInitialValues(
      language == null ? {} : {'app_language': language});
  final prefs = await SharedPreferences.getInstance();
  return ProviderScope(
    overrides: [
      sharedPreferencesProvider.overrideWithValue(prefs),
      apiClientProvider.overrideWithValue(
        ApiClient(client: client, tokenStore: TokenStore(prefs), baseUrl: 'http://test'),
      ),
    ],
    child: const KnowWeaveApp(),
  );
}

http.Response _json(Object data, int status) => http.Response(
      jsonEncode(data),
      status,
      headers: {'content-type': 'application/json; charset=utf-8'},
    );

http.Client _happyClient() => MockClient((request) async {
      switch (request.url.path) {
        case '/auth/login':
          return _json({'token': 't', 'user_id': '1', 'username': 'alice'}, 200);
        case '/notes':
          return _json([], 200);
        default:
          return _json({'detail': 'not found'}, 404);
      }
    });

/// 登录成功并落到笔记页。
///
/// 默认强制简体中文，便于断言既有中文文案；language 为 null 表示跟随系统。
/// 登录按钮按控件类型定位，避免依赖当前语言的按钮文案。
Future<void> _login(WidgetTester tester, {String? language = 'zhHans'}) async {
  final app = await buildTestApp(client: _happyClient(), language: language);
  await tester.pumpWidget(app);
  await tester.pumpAndSettle();
  await tester.enterText(find.byType(TextField).at(0), 'alice');
  await tester.enterText(find.byType(TextField).at(1), 'secret123');
  await tester.tap(find.byType(FilledButton));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('底栏三页：笔记 / AI 助手 / 我的', (tester) async {
    await _login(tester);
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('笔记'), findsOneWidget);
    expect(find.text('AI 助手'), findsOneWidget);
    expect(find.text('我的'), findsOneWidget);

    // 切到「我的」：显示账号 + 外观 + 语言
    await tester.tap(find.text('我的'));
    await tester.pumpAndSettle();
    expect(find.text('alice'), findsOneWidget);
    expect(find.text('外观'), findsOneWidget);
    expect(find.text('语言'), findsOneWidget);

    // 切到「AI 助手」：欢迎语
    await tester.tap(find.text('AI 助手'));
    await tester.pumpAndSettle();
    expect(find.text('AI 学习助手'), findsOneWidget);
    expect(find.textContaining('输入你的学习目标'), findsOneWidget);
  });

  testWidgets('笔记编辑页设置的草稿目标 → AI 页自动发送', (tester) async {
    final client = MockClient((request) async {
      switch (request.url.path) {
        case '/auth/login':
          return _json({'token': 't', 'user_id': '1', 'username': 'alice'}, 200);
        case '/notes':
          return _json([], 200);
        case '/agent/sessions':
          return _json({
            'session_id': 's1',
            'summary': '已开始复习',
            'plan': const [],
            'steps': const [],
            'conversation': const [],
          }, 201);
        default:
          return _json({'detail': 'not found'}, 404);
      }
    });
    await tester.pumpWidget(
        await buildTestApp(client: client, language: 'zhHans'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), 'alice');
    await tester.enterText(find.byType(TextField).at(1), 'secret123');
    await tester.tap(find.text('登 录'));
    await tester.pumpAndSettle();

    // 先切到 AI 助手页（懒构建：首次访问才会创建 AgentChatScreen）
    await tester.tap(find.text('AI 助手'));
    await tester.pumpAndSettle();

    // 模拟笔记编辑页设置草稿目标（其 AI 按钮的行为）
    final container = ProviderScope.containerOf(
        tester.element(find.byType(NavigationBar)));
    container.read(agentDraftGoalProvider.notifier).state = '围绕笔记《X》帮我复习';
    await tester.pumpAndSettle();

    expect(find.text('已开始复习'), findsOneWidget);
  });

  testWidgets('未登录时重定向到登录页', (tester) async {
    final client = MockClient((_) async => _json({}, 404));
    await tester.pumpWidget(
        await buildTestApp(client: client, language: 'zhHans'));
    await tester.pumpAndSettle();
    expect(find.text('登 录'), findsOneWidget);
  });

  testWidgets('登录失败提示后端返回的错误信息', (tester) async {
    final client = MockClient((request) async {
      if (request.url.path == '/auth/login') {
        return _json({'detail': '用户名或密码错误'}, 401);
      }
      return _json({}, 404);
    });
    await tester.pumpWidget(
        await buildTestApp(client: client, language: 'zhHans'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).at(0), 'alice');
    await tester.enterText(find.byType(TextField).at(1), 'wrong');
    await tester.tap(find.text('登 录'));
    await tester.pumpAndSettle();

    expect(find.text('用户名或密码错误'), findsOneWidget);
    expect(find.text('我的笔记'), findsNothing);
  });

  testWidgets('把语言切成 English 后界面文案变为英文', (tester) async {
    await _login(tester);
    expect(find.text('笔记'), findsOneWidget);

    await tester.tap(find.text('我的'));
    await tester.pumpAndSettle();

    // 语言卡片在列表下方，先滚动到可见
    await tester.drag(find.byType(ListView), const Offset(0, -300));
    await tester.pumpAndSettle();
    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();

    // 底栏与页面标题应切换为英文，且不再出现中文文案
    expect(find.text('Notes'), findsOneWidget);
    expect(find.text('Assistant'), findsOneWidget);
    expect(find.text('Profile'), findsWidgets);
    expect(find.text('笔记'), findsNothing);
    expect(find.text('退出登录'), findsNothing);
  });

  testWidgets('界面语言会作为 Accept-Language 随请求发出', (tester) async {
    final tags = <String?>[];
    final client = MockClient((request) async {
      tags.add(request.headers['Accept-Language']);
      if (request.url.path == '/auth/login') {
        return _json({'token': 't', 'user_id': '1', 'username': 'alice'}, 200);
      }
      return _json([], 200);
    });

    await tester.pumpWidget(
        await buildTestApp(client: client, language: 'zhHans'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), 'alice');
    await tester.enterText(find.byType(TextField).at(1), 'secret123');
    await tester.tap(find.byType(FilledButton));
    await tester.pumpAndSettle();

    expect(tags, isNotEmpty);
    // BCP 47：简体中文用脚本子标签 zh-Hans，而非地区形式 zh-CN
    expect(tags.first, 'zh-Hans');
  });

  testWidgets('跟随系统且系统为英文时，请求头为 en', (tester) async {
    tester.platformDispatcher.localeTestValue = const Locale('en');
    addTearDown(tester.platformDispatcher.clearLocaleTestValue);

    final tags = <String?>[];
    final client = MockClient((request) async {
      tags.add(request.headers['Accept-Language']);
      if (request.url.path == '/auth/login') {
        return _json({'token': 't', 'user_id': '1', 'username': 'alice'}, 200);
      }
      return _json([], 200);
    });

    await tester.pumpWidget(await buildTestApp(client: client, language: null));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), 'alice');
    await tester.enterText(find.byType(TextField).at(1), 'secret123');
    await tester.tap(find.byType(FilledButton));
    await tester.pumpAndSettle();

    expect(tags, isNotEmpty);
    expect(tags.first, 'en');
  });

  testWidgets('跟随系统时按系统语言显示（系统为英文）', (tester) async {
    tester.platformDispatcher.localeTestValue = const Locale('en');
    addTearDown(tester.platformDispatcher.clearLocaleTestValue);

    await _login(tester, language: null);
    expect(find.text('Notes'), findsOneWidget);
    expect(find.text('笔记'), findsNothing);
  });
}
