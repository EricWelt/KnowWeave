import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/widgets/thinking_indicator.dart';
import '../agent_provider.dart';
import 'widgets/chat_bubble.dart';

/// AI 学习助手页（底栏第二页）。
class AgentChatScreen extends ConsumerStatefulWidget {
  const AgentChatScreen({super.key});

  @override
  ConsumerState<AgentChatScreen> createState() => _AgentChatScreenState();
}

class _AgentChatScreenState extends ConsumerState<AgentChatScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  bool _handlingDraft = false;

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_scroll.hasClients) return;
      final position = _scroll.position;
      // 列表尚无内容/未完成布局时跳过，避免渲染期断言
      if (!position.hasContentDimensions || position.maxScrollExtent <= 0) {
        return;
      }
      _scroll.animateTo(
        position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _send() async {
    final text = _input.text;
    if (text.trim().isEmpty) return;
    _input.clear();
    await ref.read(agentChatProvider.notifier).send(text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(agentChatProvider);

    // 消费笔记编辑页设置的「围绕当前笔记复习」目标
    ref.listen<String?>(agentDraftGoalProvider, (prev, next) {
      if (next != null && next.isNotEmpty) {
        final goal = next;
        ref.read(agentDraftGoalProvider.notifier).state = null;
        Future.microtask(() async {
          await ref.read(agentChatProvider.notifier).send(goal);
          _scrollToBottom();
        });
      }
    });
    final draft = ref.read(agentDraftGoalProvider);
    if (draft != null && draft.isNotEmpty && !_handlingDraft) {
      _handlingDraft = true;
      final goal = draft;
      ref.read(agentDraftGoalProvider.notifier).state = null;
      Future.microtask(() async {
        await ref.read(agentChatProvider.notifier).send(goal);
        _handlingDraft = false;
        _scrollToBottom();
      });
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 学习助手'),
        actions: [
          if (state.sessions.isNotEmpty)
            PopupMenuButton<String>(
              icon: const Icon(Icons.history),
              tooltip: '历史会话',
              onSelected: (sid) async {
                await ref.read(agentChatProvider.notifier).loadHistory(sid);
                _scrollToBottom();
              },
              itemBuilder: (_) => [
                for (final s in state.sessions)
                  PopupMenuItem(
                    value: s.id,
                    child: Text(
                      s.goal.length > 20 ? '${s.goal.substring(0, 20)}…' : s.goal,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
            ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: state.messages.isEmpty
                ? const _Welcome()
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
                    itemCount: state.messages.length,
                    itemBuilder: (context, index) {
                      final msg = state.messages[index];
                      return ChatBubble(
                        message: msg,
                        onAnswer: (answers) async {
                          await ref
                              .read(agentChatProvider.notifier)
                              .submitAnswers(answers);
                          _scrollToBottom();
                        },
                      );
                    },
                  ),
          ),
          // 「思考中」动画指示（替代加载条）
          if (state.loading)
            Align(
              alignment: Alignment.centerLeft,
              child: Padding(
                padding: const EdgeInsets.only(left: 20, bottom: 4),
                child: ThinkingIndicator(),
              ),
            ),
          _InputBar(controller: _input, onSend: _send),
        ],
      ),
    );
  }
}

class _Welcome extends StatelessWidget {
  const _Welcome();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.auto_awesome, size: 56, color: scheme.primary),
            const SizedBox(height: 16),
            Text('输入你的学习目标',
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Text('例如："帮我复习操作系统第三章"',
                style: TextStyle(color: scheme.onSurfaceVariant)),
            const SizedBox(height: 8),
            Text('Agent 会自主规划：检索笔记 → 生成摘要 → 出题 → 解释概念',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, color: scheme.outline)),
          ],
        ),
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  const _InputBar({required this.controller, required this.onSend});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 6, 12, 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                minLines: 1,
                maxLines: 4,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSend(),
                decoration: const InputDecoration(
                  hintText: '输入学习目标或问题…',
                  isDense: true,
                  filled: true,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.all(Radius.circular(24)),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              icon: const Icon(Icons.send),
              tooltip: '发送',
              onPressed: onSend,
            ),
          ],
        ),
      ),
    );
  }
}