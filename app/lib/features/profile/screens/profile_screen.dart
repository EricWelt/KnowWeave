import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/l10n.dart';
import '../../../core/router/app_router.dart';
import '../../../main.dart';
import '../../auth/auth_provider.dart';

/// 「我的」页：账号信息 + 外观 + 语言 + 退出登录。
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authStateProvider);
    final themeMode = ref.watch(themeModeProvider);
    final language = ref.watch(appLanguageProvider);
    final scheme = Theme.of(context).colorScheme;
    final l10n = context.l10n;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.profileTitle)),
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
              title: Text(auth.username ?? l10n.notSignedIn,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Text(l10n.profileSubtitle),
            ),
          ),
          const SizedBox(height: 12),
          // ---- 外观 ----
          Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 4),
                  child: Text(l10n.appearanceSection,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                  child: SegmentedButton<ThemeMode>(
                    segments: [
                      ButtonSegment(
                          value: ThemeMode.light,
                          icon: const Icon(Icons.light_mode_outlined),
                          label: Text(l10n.themeLight)),
                      ButtonSegment(
                          value: ThemeMode.dark,
                          icon: const Icon(Icons.dark_mode_outlined),
                          label: Text(l10n.themeDark)),
                      ButtonSegment(
                          value: ThemeMode.system,
                          icon: const Icon(Icons.brightness_auto_outlined),
                          label: Text(l10n.themeSystem)),
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
          // ---- 语言 ----
          Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 4),
                  child: Text(l10n.languageSection,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                  child: SegmentedButton<AppLanguage>(
                    segments: [
                      ButtonSegment(
                          value: AppLanguage.system,
                          icon: const Icon(Icons.language_outlined),
                          label: Text(l10n.languageSystem)),
                      ButtonSegment(
                          value: AppLanguage.en,
                          label: Text(l10n.languageEnglish)),
                      ButtonSegment(
                          value: AppLanguage.zhHans,
                          label: Text(l10n.languageChineseSimplified)),
                    ],
                    selected: {language},
                    onSelectionChanged: (selection) =>
                        ref.read(appLanguageProvider.notifier).set(selection.first),
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
                ListTile(
                  leading: const Icon(Icons.info_outline),
                  title: Text(l10n.aboutSection),
                  subtitle: Text(l10n.aboutSubtitle),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: Icon(Icons.logout, color: scheme.error),
                  title:
                      Text(l10n.signOut, style: TextStyle(color: scheme.error)),
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
