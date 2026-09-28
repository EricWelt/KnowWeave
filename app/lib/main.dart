import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core/l10n/l10n.dart';
import 'core/providers.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'l10n/generated/app_localizations.dart';

/// 主题模式（亮/暗/跟随系统），持久化到本地。
final themeModeProvider = NotifierProvider<ThemeModeNotifier, ThemeMode>(
  ThemeModeNotifier.new,
);

class ThemeModeNotifier extends Notifier<ThemeMode> {
  static const _key = 'theme_mode';

  @override
  ThemeMode build() {
    final prefs = ref.watch(sharedPreferencesProvider);
    final saved = prefs.getString(_key);
    return switch (saved) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  Future<void> set(ThemeMode mode) async {
    state = mode;
    await ref.read(sharedPreferencesProvider).setString(_key, mode.name);
  }
}

/// 界面语言，持久化到本地；默认跟随系统。
final appLanguageProvider =
    NotifierProvider<AppLanguageNotifier, AppLanguage>(
  AppLanguageNotifier.new,
);

class AppLanguageNotifier extends Notifier<AppLanguage> {
  static const _key = 'app_language';

  @override
  AppLanguage build() {
    final prefs = ref.watch(sharedPreferencesProvider);
    return AppLanguage.fromStorage(prefs.getString(_key));
  }

  Future<void> set(AppLanguage language) async {
    state = language;
    await ref.read(sharedPreferencesProvider).setString(_key, language.name);
  }
}

/// 当前生效的界面语言。
///
/// 手动选择时取选项本身；跟随系统时用平台语言解析到受支持的语言，
/// 与 MaterialApp 内部的解析规则一致。
final effectiveLocaleProvider = Provider<Locale>((ref) {
  final explicit = ref.watch(appLanguageProvider).locale;
  if (explicit != null) return explicit;
  return basicLocaleListResolution(
    WidgetsBinding.instance.platformDispatcher.locales,
    AppLocalizations.supportedLocales,
  );
});

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  runApp(
    ProviderScope(
      overrides: [sharedPreferencesProvider.overrideWithValue(prefs)],
      child: const KnowWeaveApp(),
    ),
  );
}

class KnowWeaveApp extends ConsumerWidget {
  const KnowWeaveApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final themeMode = ref.watch(themeModeProvider);
    final language = ref.watch(appLanguageProvider);

    // 把生效语言同步给 ApiClient（决定请求头 Accept-Language）。
    //
    // effectiveLocaleProvider 依赖 appLanguageProvider，语言一变本组件就会重建，
    // 因此这里直接赋值即可，无需再注册监听。用赋值而不是让 providers.dart 反向
    // 依赖本文件，是为了避免 main.dart 与 providers.dart 互相导入。
    ref.read(apiClientProvider).languageTag =
        ref.watch(effectiveLocaleProvider).languageTag;
    return MaterialApp.router(
      title: 'KnowWeave',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeMode,
      locale: language.locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      routerConfig: router,
    );
  }
}
