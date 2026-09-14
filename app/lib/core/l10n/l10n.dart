import 'package:flutter/widgets.dart';

import '../../l10n/generated/app_localizations.dart';

/// 界面语言选项。
///
/// 语言标签遵循 BCP 47：英文 `en`，简体中文 `zh-Hans`
/// （简繁之别是书写脚本之别，故用 Hans 脚本子标签而非地区子标签）。
enum AppLanguage {
  /// 跟随系统；交给 MaterialApp 解析，此时不指定 locale。
  system,
  en,
  zhHans;

  /// 传给 MaterialApp 的 locale；null 表示跟随系统。
  Locale? get locale => switch (this) {
        AppLanguage.en => const Locale('en'),
        AppLanguage.zhHans =>
          Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hans'),
        AppLanguage.system => null,
      };

  /// 从本地存储值还原；未知值回落「跟随系统」。
  static AppLanguage fromStorage(String? value) => AppLanguage.values
      .firstWhere((e) => e.name == value, orElse: () => AppLanguage.system);
}

/// 取当前语言资源：`context.l10n.loginButton`
extension L10nX on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}
