import 'package:flutter/material.dart';

import '../../../../core/widgets/markdown_view.dart';
import '../../models/agent_models.dart';
import 'quiz_card.dart';

/// 聊天气泡：用户/助手/工具卡片/题目卡片/结果卡片。
class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  final Future<void> Function(List<QuizAnswer> answers) onAnswer;

  const ChatBubble({super.key, required this.message, required this.onAnswer});

  @override
  Widget build(BuildContext context) {
    switch (message.type) {
      case ChatMsgType.tool:
        return _ToolCard(summary: message.content);
      case ChatMsgType.quiz:
        return QuizCard(
          questions: message.questions ?? const [],
          onAnswer: onAnswer,
        );
      case ChatMsgType.quizResult:
        return _QuizResultCard(result: message.quizResult!);
      case ChatMsgType.thinking:
        return _ThinkingCard(steps: message.thinkingSteps ?? const []);
      case ChatMsgType.user:
      case ChatMsgType.assistant:
        return _TextBubble(message: message);
    }
  }
}

class _TextBubble extends StatelessWidget {
  final ChatMessage message;
  const _TextBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isUser = message.type == ChatMsgType.user;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 5),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.84),
        decoration: BoxDecoration(
          color: isUser
              ? scheme.primaryContainer
              : scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 16),
          ),
        ),
        child: isUser
            ? Text(message.content,
                style: TextStyle(color: scheme.onPrimaryContainer, height: 1.5))
            : MarkdownView(data: message.content, scrollable: false),
      ),
    );
  }
}

class _ToolCard extends StatelessWidget {
  final String summary;
  const _ToolCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      color: scheme.surfaceContainerLow,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          children: [
            Icon(Icons.build_circle_outlined,
                size: 18, color: scheme.primary),
            const SizedBox(width: 8),
            Expanded(
              child: Text(summary,
                  style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuizResultCard extends StatelessWidget {
  final QuizResult result;
  const _QuizResultCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final ratio = result.total == 0 ? 0.0 : result.correct / result.total;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      color: scheme.primaryContainer.withValues(alpha: 0.5),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.emoji_events_outlined, color: scheme.primary),
                const SizedBox(width: 8),
                Text('答题结果',
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                Text('${result.correct}/${result.total}',
                    style: TextStyle(
                        fontWeight: FontWeight.bold, color: scheme.primary)),
              ],
            ),
            const SizedBox(height: 10),
            LinearProgressIndicator(
              value: ratio,
              borderRadius: BorderRadius.circular(6),
              minHeight: 8,
            ),
            const SizedBox(height: 10),
            Text('主题掌握度：${(result.masteryLevel * 100).toStringAsFixed(0)}%',
                style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
            if (result.weakPoints.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text('薄弱点：${result.weakPoints.join('、')}',
                  style: TextStyle(
                      fontSize: 13, color: scheme.error, height: 1.4)),
            ],
          ],
        ),
      ),
    );
  }
}
/// 可折叠的「思考过程」卡片（类似 LLM 深度思考展示）。
class _ThinkingCard extends StatelessWidget {
  final List<String> steps;
  const _ThinkingCard({required this.steps});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      color: scheme.surfaceContainerLow,
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 14),
        childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
        leading: Icon(Icons.psychology_outlined,
            size: 20, color: scheme.primary),
        title: const Text('思考过程',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
        subtitle: Text('${steps.length} 个推理步骤',
            style: TextStyle(fontSize: 11, color: scheme.outline)),
        children: [
          for (final s in steps)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (s.startsWith('🔧'))
                    Icon(Icons.build_circle_outlined,
                        size: 15, color: scheme.tertiary)
                  else
                    Icon(Icons.auto_awesome, size: 13, color: scheme.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(s,
                        style: TextStyle(
                            fontSize: 12.5,
                            height: 1.5,
                            color: scheme.onSurfaceVariant)),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}