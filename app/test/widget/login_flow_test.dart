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

Future<Widget> buildTestApp({required http.Client client}) async {
  SharedPreferences.setMockInitialValues({});
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

/// 登录成功并落到笔记页的公共流程
Future<ProviderScope> _login(WidgetTester tester) async {
  final client = MockClient((request) async {
    switch (request.url.path) {
      case '/auth/login':
        return _json({'token': 't', 'user_id': '1', 'username': 'alice'}, 200);
      case '/notes':
        return _json([], 200);
      default:
        return _json({'detail': 'not found'}, 404);
    }
  });
  final app = await buildTestApp(client: client);
  await tester.pumpWidget(app);
  await tester.pumpAndSettle();
  await tester.enterText(find.byType(TextField).at(0), 'alice');
  await tester.enterText(find.byType(TextField).at(1), 'secret123');
  await tester.tap(find.text('登 录'));
  await tester.pumpAndSettle();
  return app as ProviderScope;
}

void main() {
  testWidgets('底栏三页：笔记 / AI 助手 / 我的', (tester) async {
    await _login(tester);
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('笔记'), findsOneWidget);
    expect(find.text('AI 助手'), findsOneWidget);
    expect(find.text('我的'), findsOneWidget);

    // 切到「我的」：显示账号 + 外观
    await tester.tap(find.text('我的'));
    await tester.pumpAndSettle();
    expect(find.text('alice'), findsOneWidget);
    expect(find.text('外观'), findsOneWidget);

    // 切到「AI 助手」：欢迎语
    await tester.tap(find.text('AI 助手'));
    await tester.pumpAndSettle();
    expect(find.text('AI 学习助手'), findsOneWidget);
    expect(find.textContaining('输入你的学习目标'), findsOneWidget);
  });

  testWidgets('笔记编辑页设置的草稿目标 → AI 页自动发送', (tester) async {
    // Mock：/agent/sessions 返回一个完整会话
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
    final app = await buildTestApp(client: client);
    await tester.pumpWidget(app);
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

    // 应自动发送并展示 assistant 回复
    expect(find.text('已开始复习'), findsOneWidget);
  });

  testWidgets('未登录时重定向到登录页', (tester) async {
    final client = MockClient((_) async => _json({}, 404));
    await tester.pumpWidget(await buildTestApp(client: client));
    await tester.pumpAndSettle();
    expect(find.text('登 录'), findsOneWidget);
  });

  testWidgets('登录失败提示错误信息', (tester) async {
    final client = MockClient((request) async {
      if (request.url.path == '/auth/login') {
        return _json({'detail': '用户名或密码错误'}, 401);
      }
      return _json({}, 404);
    });
    await tester.pumpWidget(await buildTestApp(client: client));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).at(0), 'alice');
    await tester.enterText(find.byType(TextField).at(1), 'wrong');
    await tester.tap(find.text('登 录'));
    await tester.pumpAndSettle();

    expect(find.text('用户名或密码错误'), findsOneWidget);
    expect(find.text('我的笔记'), findsNothing);
  });
}