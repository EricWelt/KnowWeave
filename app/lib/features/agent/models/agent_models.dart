// Agent 域模型集合。

/// 会话消息类型
enum ChatMsgType { user, assistant, tool, quiz, quizResult, thinking }

/// 聊天消息（含可选载荷）
class ChatMessage {
  final ChatMsgType type;
  final String content;

  /// 出题工具返回的题目
  final List<QuizQuestion>? questions;

  /// 作答结果
  final QuizResult? quizResult;

  /// 本轮 ReAct 的思考过程（think 步骤文本 + 工具调用）
  final List<String>? thinkingSteps;

  const ChatMessage(this.type, this.content,
      {this.questions, this.quizResult, this.thinkingSteps});
}

/// 选择题
class QuizQuestion {
  final String question;
  final List<String> options;
  final String answer;
  final String explanation;

  const QuizQuestion({
    required this.question,
    required this.options,
    required this.answer,
    required this.explanation,
  });

  factory QuizQuestion.fromJson(Map<String, dynamic> json) => QuizQuestion(
        question: json['question']?.toString() ?? '',
        options: (json['options'] as List? ?? [])
            .map((e) => e.toString())
            .toList(),
        answer: json['answer']?.toString() ?? '',
        explanation: json['explanation']?.toString() ?? '',
      );
}

/// 作答记录（上报后端）
class QuizAnswer {
  final String question;
  final String selected;
  final String correct;
  final bool isCorrect;

  const QuizAnswer({
    required this.question,
    required this.selected,
    required this.correct,
    required this.isCorrect,
  });

  Map<String, dynamic> toJson() => {
        'question': question,
        'selected': selected,
        'correct': correct,
        'is_correct': isCorrect,
      };
}

/// 作答结果（后端返回）
class QuizResult {
  final int correct;
  final int total;
  final double masteryLevel;
  final List<String> weakPoints;

  const QuizResult({
    required this.correct,
    required this.total,
    required this.masteryLevel,
    required this.weakPoints,
  });

  factory QuizResult.fromJson(Map<String, dynamic> json) => QuizResult(
        correct: (json['correct'] as num?)?.toInt() ?? 0,
        total: (json['total'] as num?)?.toInt() ?? 0,
        masteryLevel: (json['mastery_level'] as num?)?.toDouble() ?? 0,
        weakPoints: (json['weak_points'] as List? ?? [])
            .map((e) => e.toString())
            .toList(),
      );
}

/// Agent 执行步骤摘要
class AgentStepInfo {
  final int step;
  final String type;
  final String summary;
  final String? tool;

  const AgentStepInfo({
    required this.step,
    required this.type,
    required this.summary,
    this.tool,
  });

  factory AgentStepInfo.fromJson(Map<String, dynamic> json) => AgentStepInfo(
        step: (json['step'] as num?)?.toInt() ?? 0,
        type: json['type']?.toString() ?? '',
        summary: json['summary']?.toString() ?? '',
        tool: json['tool']?.toString(),
      );
}

/// 评测摘要
class EvalSummary {
  final double? taskCompletionRate;
  final double? toolCallSuccessRate;
  final double? avgLatencyMs;
  final double? planDeviationRate;

  const EvalSummary({
    this.taskCompletionRate,
    this.toolCallSuccessRate,
    this.avgLatencyMs,
    this.planDeviationRate,
  });

  factory EvalSummary.fromJson(Map<String, dynamic> json) => EvalSummary(
        taskCompletionRate: (json['task_completion_rate'] as num?)?.toDouble(),
        toolCallSuccessRate: (json['tool_call_success_rate'] as num?)?.toDouble(),
        avgLatencyMs: (json['avg_latency_ms'] as num?)?.toDouble(),
        planDeviationRate: (json['plan_deviation_rate'] as num?)?.toDouble(),
      );
}

/// 一次会话的完整结果（POST /agent/sessions 返回）
class AgentSessionResult {
  final String sessionId;
  final String summary;
  final List<dynamic> plan;
  final List<AgentStepInfo> steps;
  final EvalSummary? eval;
  final List<dynamic> conversation;

  const AgentSessionResult({
    required this.sessionId,
    required this.summary,
    required this.plan,
    required this.steps,
    this.eval,
    required this.conversation,
  });

  factory AgentSessionResult.fromJson(Map<String, dynamic> json) {
    return AgentSessionResult(
      sessionId: json['session_id']?.toString() ?? '',
      summary: json['summary']?.toString() ?? '',
      plan: json['plan'] as List? ?? const [],
      steps: (json['steps'] as List? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(AgentStepInfo.fromJson)
          .toList(),
      eval: json['eval'] is Map
          ? EvalSummary.fromJson((json['eval'] as Map).cast<String, dynamic>())
          : null,
      conversation: json['conversation'] as List? ?? const [],
    );
  }
}

/// 会话列表项
class AgentSessionSummary {
  final String id;
  final String goal;
  final String status;
  final String? createdAt;

  const AgentSessionSummary({
    required this.id,
    required this.goal,
    required this.status,
    this.createdAt,
  });

  factory AgentSessionSummary.fromJson(Map<String, dynamic> json) =>
      AgentSessionSummary(
        id: json['id']?.toString() ?? '',
        goal: json['goal']?.toString() ?? '',
        status: json['status']?.toString() ?? '',
        createdAt: json['created_at']?.toString(),
      );
}