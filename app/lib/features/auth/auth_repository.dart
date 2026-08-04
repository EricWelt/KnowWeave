import '../../core/network/api_client.dart';

/// 登录返回的会话信息
class AuthSession {
  final String token;
  final String userId;
  final String username;

  AuthSession({required this.token, required this.userId, required this.username});

  factory AuthSession.fromJson(Map<String, dynamic> json) => AuthSession(
        token: json['token']?.toString() ?? '',
        userId: json['user_id']?.toString() ?? '',
        username: json['username']?.toString() ?? '',
      );
}

/// 认证数据访问层。
class AuthRepository {
  final ApiClient _api;
  AuthRepository(this._api);

  Future<AuthSession> login(String username, String password) async {
    final data = await _api.post('/auth/login',
        body: {'username': username, 'password': password});
    return AuthSession.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<void> register(String username, String password) async {
    await _api.post('/auth/register',
        body: {'username': username, 'password': password});
  }
}
