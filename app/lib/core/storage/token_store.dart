import 'package:shared_preferences/shared_preferences.dart';

/// 本地登录态存储（JWT + 用户信息）。
class TokenStore {
  static const _kToken = 'jwt_token';
  static const _kUserId = 'user_id';
  static const _kUsername = 'username';

  final SharedPreferences _prefs;
  TokenStore(this._prefs);

  String? get token => _prefs.getString(_kToken);
  String? get userId => _prefs.getString(_kUserId);
  String? get username => _prefs.getString(_kUsername);

  bool get isLoggedIn {
    final t = token;
    return t != null && t.isNotEmpty;
  }

  Future<void> save({
    required String token,
    required String userId,
    required String username,
  }) async {
    await _prefs.setString(_kToken, token);
    await _prefs.setString(_kUserId, userId);
    await _prefs.setString(_kUsername, username);
  }

  Future<void> clear() async {
    await _prefs.remove(_kToken);
    await _prefs.remove(_kUserId);
    await _prefs.remove(_kUsername);
  }
}
