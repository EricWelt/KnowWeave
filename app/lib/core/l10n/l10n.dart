import 'package:flutter/widgets.dart';

import '../../l10n/generated/app_localizations.dart';
import '../network/api_exception.dart';

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

/// BCP 47 语言标签，用于 HTTP `Accept-Language`（如 `en` / `zh-Hans`）。
extension LocaleTagX on Locale {
  String get languageTag => scriptCode == null || scriptCode!.isEmpty
      ? languageCode
      : '$languageCode-$scriptCode';
}

/// 取当前语言资源：`context.l10n.loginButton`
extension L10nX on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}

/// 把异常转成可展示文案。
///
/// 后端返回的 `detail` 原样显示（服务端本地化在 Phase B 完成）；
/// 没有 detail 时按 HTTP 状态码给出本地化文案。
String describeApiError(BuildContext context, Object error) {
  if (error is ApiException) {
    if (error.message.isNotEmpty) return error.message;
    return context.l10n.requestFailed(error.statusCode ?? 0);
  }
  return error.toString();
}
