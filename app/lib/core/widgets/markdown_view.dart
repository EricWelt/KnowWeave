import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_markdown_plus_latex/flutter_markdown_plus_latex.dart';
import 'package:markdown/markdown.dart' as md;

/// 统一的 Markdown + LaTeX 渲染组件（全 App 共用，避免重复实现）。
class MarkdownView extends StatelessWidget {
  final String data;
  final bool selectable;
  final EdgeInsets padding;

  /// 是否内部滚动。聊天气泡内嵌套时必须设为 false：
  /// Markdown 内部是 ListView，嵌套在 ListView item 里会触发
  /// unbounded height 崩溃；由外层滚动容器接管即可。
  final bool scrollable;

  const MarkdownView({
    super.key,
    required this.data,
    this.selectable = true,
    this.padding = EdgeInsets.zero,
    this.scrollable = true,
  });

  @override
  Widget build(BuildContext context) {
    return Markdown(
      data: data,
      selectable: selectable,
      padding: padding,
      // 非滚动模式：Markdown 内部 ListView 用 shrinkWrap 包裹，
      // 避免嵌套在外部 ListView item 时触发 unbounded height
      shrinkWrap: !scrollable,
      physics: scrollable ? null : const NeverScrollableScrollPhysics(),
      styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
        p: const TextStyle(height: 1.6),
        code: TextStyle(
          backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
          fontFamily: 'monospace',
          fontSize: 13,
        ),
      ),
      builders: {
        'latex': LatexElementBuilder(
          textStyle: const TextStyle(fontWeight: FontWeight.w500),
        ),
      },
      extensionSet: md.ExtensionSet(
        [...md.ExtensionSet.gitHubFlavored.blockSyntaxes, LatexBlockSyntax()],
        [...md.ExtensionSet.gitHubFlavored.inlineSyntaxes, LatexInlineSyntax()],
      ),
    );
  }
}