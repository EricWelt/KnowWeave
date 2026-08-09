import 'package:flutter/material.dart';

/// AI 思考中的动画指示：三个依次脉动的圆点 + 文案。
class ThinkingIndicator extends StatefulWidget {
  final String text;
  const ThinkingIndicator({super.key, this.text = 'AI 思考中…'});

  @override
  State<ThinkingIndicator> createState() => _ThinkingIndicatorState();
}

class _ThinkingIndicatorState extends State<ThinkingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 三个错相脉动的圆点
          for (var i = 0; i < 3; i++)
            AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                final phase = ((_controller.value + i * 0.33) % 1.0);
                final scale = 0.6 + 0.4 * phase;
                final opacity = 0.35 + 0.65 * phase;
                return Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: scheme.primary.withValues(alpha: opacity),
                  ),
                  transform: Matrix4.diagonal3Values(scale, scale, 1),
                );
              },
            ),
          const SizedBox(width: 10),
          Text(widget.text,
              style: TextStyle(
                  fontSize: 13, color: scheme.onSurfaceVariant)),
        ],
      ),
    );
  }
}