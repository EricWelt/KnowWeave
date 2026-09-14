import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:know_weave/core/l10n/l10n.dart';

Map<String, dynamic> _readArb(String path) =>
    jsonDecode(File(path).readAsStringSync()) as Map<String, dynamic>;

/// 去掉以 @ 开头的元数据项，只留真正的文案键。
Set<String> _messageKeys(Map<String, dynamic> arb) =>
    arb.keys.where((k) => !k.startsWith('@')).toSet();

void main() {
  group('ARB 资源一致性', () {
    test('英文与简体中文的文案键集合完全一致', () {
      final en = _messageKeys(_readArb('lib/l10n/app_en.arb'));
      final zh = _messageKeys(_readArb('lib/l10n/app_zh_Hans.arb'));
      expect(zh.difference(en), isEmpty, reason: '中文存在英文模板未定义的键');
      expect(en.difference(zh), isEmpty, reason: '英文存在中文未翻译的键');
      expect(en, isNotEmpty);
    });

    test('中文基语言文件与 zh_Hans 文件内容一致', () {
      // Flutter 要求：出现脚本子标签时必须有基语言兜底文件（app_zh.arb）。
      // 本项目目前只有简体一种中文变体，因此两者内容必须完全相同；
      // 将来若增加繁体（zh_Hant），应改为让基语言文件只保留共用文案。
      final base = _readArb('lib/l10n/app_zh.arb');
      final hans = _readArb('lib/l10n/app_zh_Hans.arb');
      expect(_messageKeys(base), _messageKeys(hans));
      for (final key in _messageKeys(hans)) {
        expect(base[key], hans[key], reason: '$key 在两个中文文件中不一致');
      }
    });

    test('每个文案的占位符都在模板元数据中声明', () {
      final en = _readArb('lib/l10n/app_en.arb');
      final placeholder = RegExp(r'\{(\w+)\}');
      for (final entry in en.entries) {
        if (entry.key.startsWith('@')) continue;
        final used = placeholder
            .allMatches(entry.value as String)
            .map((m) => m.group(1)!)
            .toSet();
        if (used.isEmpty) continue;
        final meta = en['@${entry.key}'];
        final declared = meta is Map && meta['placeholders'] is Map
            ? (meta['placeholders'] as Map).keys.toSet()
            : <String>{};
        expect(declared, containsAll(used),
            reason: '${entry.key} 的占位符未声明');
      }
    });
  });

  group('AppLanguage', () {
    test('语言标签按 BCP 47 映射', () {
      expect(AppLanguage.en.locale, const Locale('en'));
      expect(AppLanguage.zhHans.locale,
          Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hans'));
      expect(AppLanguage.zhHans.locale!.scriptCode, 'Hans');
    });

    test('跟随系统时不指定 locale', () {
      expect(AppLanguage.system.locale, isNull);
    });

    test('存储值往返一致，未知值回落跟随系统', () {
      for (final language in AppLanguage.values) {
        expect(AppLanguage.fromStorage(language.name), language);
      }
      expect(AppLanguage.fromStorage(null), AppLanguage.system);
      expect(AppLanguage.fromStorage('zh_CN'), AppLanguage.system);
    });
  });
}
