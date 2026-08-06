import '../../core/network/api_client.dart';
import 'models/agent_models.dart';

/// Agent 数据访问层。
class AgentRepository {
  final ApiClient _api;
  AgentRepository(this._api);

  Future<AgentSessionResult> createSession(String goal) async {
    final data = await _api.post('/agent/sessions', body: {'goal': goal});
    return AgentSessionResult.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<AgentSessionResult> continueChat(String sessionId, String message) async {
    final data = await _api.post('/agent/sessions/$sessionId/chat',
        body: {'message': message});
    return AgentSessionResult.fromJson({
      'session_id': (data as Map)['session_id'],
      'summary': data['reply'],
      'plan': const [],
      'steps': const [],
      'conversation': data['conversation'] ?? const [],
    });
  }

  Future<List<AgentSessionSummary>> listSessions() async {
    final data = await _api.get('/agent/sessions');
    return (data as List)
        .map((e) => AgentSessionSummary.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  Future<List<dynamic>> getConversation(String sessionId) async {
    final data = await _api.get('/agent/sessions/$sessionId');
    return (data as Map)['conversation'] as List? ?? const [];
  }

  Future<EvalSummary> getEval(String sessionId) async {
    final data = await _api.get('/agent/sessions/$sessionId/eval');
    return EvalSummary.fromJson({
      ...((data as Map)['metrics'] as Map? ?? {}).cast<String, dynamic>(),
    });
  }

  /// 提交作答结果（答题 → 知识状态更新闭环）
  Future<QuizResult> submitAnswers(
      String sessionId, List<QuizAnswer> answers) async {
    final data = await _api.post('/agent/sessions/$sessionId/answers',
        body: {'answers': answers.map((a) => a.toJson()).toList()});
    return QuizResult.fromJson((data as Map).cast<String, dynamic>());
  }
}
