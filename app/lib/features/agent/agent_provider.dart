import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import 'agent_repository.dart';
import 'models/agent_models.dart';

/// 笔记编辑页等设置的「待发送目标」：切到 AI 页时自动发送（消费后清空）。
final agentDraftGoalProvider = StateProvider<String?>((ref) => null);

final agentRepositoryProvider = Provider<AgentRepository>(
  (ref) => AgentRepository(ref.watch(apiClientProvider)),
);

/// 从后端会话中提取 create_quiz 的题目（修复版）：
/// 工具返回格式为 [工具 create_quiz 返回]\n{"questions": [...]}。
List<QuizQuestion>? extractQuizFromConversation(List<dynamic> conversation) {
  const marker = '[工具 create_quiz 返回]';
  for (final m in conversation) {
    if (m is! Map) continue;
    if ((m['role']?.toString() ?? '') != 'user') continue;
    final content = m['content']?.toString() ?? '';
    if (!content.contains(marker)) continue;

    final idx = content.indexOf(marker) + marker.length;
    final jsonPart = content.substring(idx).trim();
    try {
      final decoded = jsonDecode(jsonPart);
      final List<dynamic> raw;
      if (decoded is List) {
        raw = decoded;
      } else if (decoded is Map && decoded['questions'] is List) {
        raw = decoded['questions'] as List;
      } else {
        continue;
      }
      final questions = raw
          .whereType<Map<String, dynamic>>()
          .map(QuizQuestion.fromJson)
          .where((q) => q.question.isNotEmpty)
          .toList();
      if (questions.isNotEmpty) return questions;
    } catch (_) {
      // 解析失败跳过该条消息
    }
  }
  return null;
}

/// Agent 对话状态
class AgentChatState {
  final String? sessionId;
  final List<ChatMessage> messages;
  final bool loading;
  final List<AgentSessionSummary> sessions;

  const AgentChatState({
    this.sessionId,
    this.messages = const [],
    this.loading = false,
    this.sessions = const [],
  });

  AgentChatState copyWith({
    String? sessionId,
    List<ChatMessage>? messages,
    bool? loading,
    List<AgentSessionSummary>? sessions,
  }) =>
      AgentChatState(
        sessionId: sessionId ?? this.sessionId,
        messages: messages ?? this.messages,
        loading: loading ?? this.loading,
        sessions: sessions ?? this.sessions,
      );
}

/// 对话状态机：发送 / 历史加载 / 提交作答。
final agentChatProvider = NotifierProvider<AgentChatNotifier, AgentChatState>(
  AgentChatNotifier.new,
);

class AgentChatNotifier extends Notifier<AgentChatState> {
  AgentRepository get _repo => ref.read(agentRepositoryProvider);

  @override
  AgentChatState build() {
    _loadSessions();
    return const AgentChatState();
  }

  Future<void> _loadSessions() async {
    try {
      final sessions = await _repo.listSessions();
      state = state.copyWith(sessions: sessions);
    } catch (_) {
      // 未登录/后端未启动：保持空列表
    }
  }

  Future<void> send(String text) async {
    final message = text.trim();
    if (message.isEmpty || state.loading) return;
    state = state.copyWith(
      messages: [...state.messages, ChatMessage(ChatMsgType.user, message)],
      loading: true,
    );
    try {
      final result = state.sessionId == null
          ? await _repo.createSession(message)
          : await _repo.continueChat(state.sessionId!, message);

      final messages = [...state.messages];

      // 思考过程（think 文本 + 工具调用），可折叠展示
      final thinking = <String>[];
      for (final s in result.steps) {
        if (s.type == 'think' && s.summary.isNotEmpty) {
          thinking.add(s.summary);
        } else if (s.type == 'act') {
          final ok = s.summary.contains('失败') ? '（失败）' : '';
          thinking.add('🔧 调用工具 ${s.tool ?? ''}$ok');
        }
      }
      if (thinking.isNotEmpty) {
        messages.add(ChatMessage(ChatMsgType.thinking, '💭 思考过程',
            thinkingSteps: thinking));
      }

      // 工具步骤卡片
      for (final s in result.steps) {
        if (s.type == 'act') {
          messages.add(ChatMessage(ChatMsgType.tool,
              '调用了 ${s.tool ?? '工具'} · ${s.summary}'));
        }
      }
      // 最终回答
      messages.add(ChatMessage(ChatMsgType.assistant, result.summary));
      // 从会话中提取题目
      final quiz = extractQuizFromConversation(result.conversation);
      if (quiz != null) {
        messages.add(ChatMessage(ChatMsgType.quiz, '📝 生成了 ${quiz.length} 道练习题',
            questions: quiz));
      }
      state = state.copyWith(
        sessionId: result.sessionId,
        messages: messages,
        loading: false,
      );
      _loadSessions();
    } catch (e) {
      state = state.copyWith(
        messages: [
          ...state.messages,
          ChatMessage(ChatMsgType.assistant, '⚠️ 调用失败：$e'),
        ],
        loading: false,
      );
    }
  }

  /// 切换历史会话
  Future<void> loadHistory(String sessionId) async {
    state = state.copyWith(sessionId: sessionId, loading: true);
    try {
      final conversation = await _repo.getConversation(sessionId);
      final messages = <ChatMessage>[];
      for (final m in conversation) {
        if (m is! Map) continue;
        final role = m['role']?.toString() ?? '';
        final content = m['content']?.toString() ?? '';
        if (role == 'user') {
          messages.add(ChatMessage(ChatMsgType.user, content));
        } else if (role == 'assistant') {
          messages.add(ChatMessage(ChatMsgType.assistant, content));
        }
      }
      final quiz = extractQuizFromConversation(conversation);
      if (quiz != null) {
        messages.add(
            ChatMessage(ChatMsgType.quiz, '📝 历史题目 ${quiz.length} 道', questions: quiz));
      }
      state = state.copyWith(messages: messages, loading: false);
    } catch (e) {
      state = state.copyWith(
          messages: [
            ...state.messages,
            ChatMessage(ChatMsgType.assistant, '⚠️ 加载历史失败：$e'),
          ],
          loading: false);
    }
  }

  /// 提交作答结果 → 显示掌握度反馈
  Future<void> submitAnswers(List<QuizAnswer> answers) async {
    final sessionId = state.sessionId;
    if (sessionId == null) return;
    try {
      final result = await _repo.submitAnswers(sessionId, answers);
      state = state.copyWith(
        messages: [
          ...state.messages,
          ChatMessage(
            ChatMsgType.quizResult,
            '答题完成：${result.correct}/${result.total} 正确',
            quizResult: result,
          ),
        ],
      );
    } catch (e) {
      state = state.copyWith(
        messages: [
          ...state.messages,
          ChatMessage(ChatMsgType.assistant, '⚠️ 提交作答失败：$e'),
        ],
      );
    }
  }
}