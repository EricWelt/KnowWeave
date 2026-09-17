import 'package:flutter/material.dart';

import '../../../../core/l10n/l10n.dart';
import '../../../../core/widgets/markdown_view.dart';
import '../../models/agent_models.dart';
import 'quiz_card.dart';

/// 聊天气泡：用户/助手/工具卡片/题目卡片/结果卡片/错误卡片/思考过程。
class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  final Future<void> Function(List<QuizAnswer> answers) onAnswer;

  const ChatBubble({super.key, required this.message, required this.onAnswer});

  @override
  Widget build(BuildContext context) {
    switch (message.type) {
      case ChatMsgType.tool:
        return _ToolCard(
            toolName: message.toolName, summary: message.toolSummary ?? '');
      case ChatMsgType.quiz:
        return QuizCard(
          questions: message.questions ?? const [],
          onAnswer: onAnswer,
        );
      case ChatMsgType.quizResult:
        return _QuizResultCard(result: message.quizResult!);
      case ChatMsgType.thinking:
        return _ThinkingCard(steps: message.thinkingSteps ?? const []);
      case ChatMsgType.error:
        return _ErrorCard(kind: message.errorKind, detail: message.content);
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

/// 请求失败提示。文案前缀按失败来源本地化，详情原样展示。
class _ErrorCard extends StatelessWidget {
  final AgentErrorKind? kind;
  final String detail;

  const _ErrorCard({this.kind, required this.detail});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final l10n = context.l10n;
    final text = switch (kind) {
      AgentErrorKind.loadHistory => l10n.errorLoadHistory(detail),
      AgentErrorKind.submitAnswers => l10n.errorSubmitAnswers(detail),
      _ => l10n.errorSend(detail),
    };
    return Align(
      alignment: Alignment.centerLeft,
      child: Card(
        margin: const EdgeInsets.symmetric(vertical: 5),
        color: scheme.errorContainer,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.error_outline, size: 18, color: scheme.error),
              const SizedBox(width: 8),
              Expanded(
                child: Text(text,
                    style: TextStyle(
                        fontSize: 13,
                        height: 1.4,
                        color: scheme.onErrorContainer)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ToolCard extends StatelessWidget {
  final String? toolName;
  final String summary;

  const _ToolCard({this.toolName, required this.summary});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final l10n = context.l10n;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      color: scheme.surfaceContainerLow,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          children: [
            Icon(Icons.build_circle_outlined, size: 18, color: scheme.primary),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                  l10n.toolCallSummary(toolName ?? l10n.toolLabel, summary),
                  style:
                      TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
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
    final l10n = context.l10n;
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
                Text(l10n.quizResultTitle,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                Text(l10n.quizScore(result.correct, result.total),
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
            Text(l10n.masteryLevel((result.masteryLevel * 100).round()),
                style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
            if (result.weakPoints.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                  l10n.weakPoints(
                      result.weakPoints.join(l10n.listSeparator)),
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
  final List<ThinkingStep> steps;
  const _ThinkingCard({required this.steps});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final l10n = context.l10n;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      color: scheme.surfaceContainerLow,
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 14),
        childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
        leading:
            Icon(Icons.psychology_outlined, size: 20, color: scheme.primary),
        title: Text(l10n.thinkingTitle,
            style: const TextStyle(
                fontSize: 13, fontWeight: FontWeight.w600)),
        subtitle: Text(l10n.thinkingStepCount(steps.length),
            style: TextStyle(fontSize: 11, color: scheme.outline)),
        children: [
          for (final s in steps)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (s.isTool)
                    Icon(Icons.build_circle_outlined,
                        size: 15, color: scheme.tertiary)
                  else
                    Icon(Icons.auto_awesome, size: 13, color: scheme.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                        s.isTool
                            ? '${l10n.toolCalled(s.toolName ?? l10n.toolLabel)}'
                                '${s.failed ? l10n.toolFailedSuffix : ''}'
                            : (s.text ?? ''),
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
