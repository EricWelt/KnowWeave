import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/router/app_router.dart';
import '../../../main.dart';
import '../../auth/auth_provider.dart';

/// 「我的」页：账号信息 + 外观设置 + 退出登录。
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authStateProvider);
    final themeMode = ref.watch(themeModeProvider);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('我的')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ---- 账号卡片 ----
          Card(
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: scheme.primaryContainer,
                child: Icon(Icons.person, color: scheme.onPrimaryContainer),
              ),
              title: Text(auth.username ?? '未登录',
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: const Text('知脉笔记 · AI 智能学习'),
            ),
          ),
          const SizedBox(height: 12),
          // ---- 外观 ----
          Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 14, 16, 4),
                  child: Text('外观',
                      style: TextStyle(fontWeight: FontWeight.w600)),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                  child: SegmentedButton<ThemeMode>(
                    segments: const [
                      ButtonSegment(
                          value: ThemeMode.light,
                          icon: Icon(Icons.light_mode_outlined),
                          label: Text('亮色')),
                      ButtonSegment(
                          value: ThemeMode.dark,
                          icon: Icon(Icons.dark_mode_outlined),
                          label: Text('暗色')),
                      ButtonSegment(
                          value: ThemeMode.system,
                          icon: Icon(Icons.brightness_auto_outlined),
                          label: Text('跟随系统')),
                    ],
                    selected: {themeMode},
                    onSelectionChanged: (selection) =>
                        ref.read(themeModeProvider.notifier).set(selection.first),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          // ---- 关于 ----
          Card(
            child: Column(
              children: [
                const ListTile(
                  leading: Icon(Icons.info_outline),
                  title: Text('关于'),
                  subtitle: Text('KnowWeave · 自研 ReAct Agent 学习系统'),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: Icon(Icons.logout, color: scheme.error),
                  title: Text('退出登录', style: TextStyle(color: scheme.error)),
                  onTap: () async {
                    await ref.read(authStateProvider.notifier).logout();
                    if (context.mounted) context.go(AppRoutes.login);
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
