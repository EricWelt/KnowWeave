import 'dart:ui';

import 'package:flutter/material.dart';

/// 玻璃质感组件（MD3 之上的点缀，非全屏滥用）。
///
/// 设计要点：
/// - 只在小面积（AppBar 背景、卡片、底部栏）使用 BackdropFilter；
/// - 提供 [enabled] 开关：性能敏感平台可整体关闭；
/// - 双层效果：底层半透明色 + 顶层 1px 高光描边，模拟玻璃边缘反光。
class Glass {
  Glass._();

  static const double defaultBlur = 14;

  /// 是否启用模糊（可在低端机/特殊平台关闭）
  static bool enabled = true;

  /// 玻璃容器：内容 + 模糊背景 + 高光描边
  static Widget container({
    required Widget child,
    double blur = defaultBlur,
    double radius = 16,
    EdgeInsetsGeometry padding = EdgeInsets.zero,
    Color? tint,
    double tintOpacity = 0.55,
  }) {
    if (!enabled) return child;
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: (tint ?? Colors.white).withValues(alpha: tintOpacity),
            borderRadius: BorderRadius.circular(radius),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.28),
              width: 0.7,
            ),
          ),
          child: child,
        ),
      ),
    );
  }

  /// 玻璃 AppBar 背景（配合 AppBarTheme 的半透明底色）
  static Widget appBarBackground(BuildContext context) {
    if (!enabled) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(
            sigmaX: defaultBlur, sigmaY: defaultBlur),
        child: Container(
          decoration: BoxDecoration(
            color: scheme.surface.withValues(alpha: 0.72),
            border: Border(
              bottom: BorderSide(
                color: scheme.outlineVariant.withValues(alpha: 0.4),
                width: 0.5,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
