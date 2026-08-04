import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import 'auth_repository.dart';

/// 认证状态
enum AuthStatus { unauthenticated, authenticated }

class AuthState {
  final AuthStatus status;
  final String? username;

  const AuthState.unauthenticated()
      : status = AuthStatus.unauthenticated,
        username = null;

  const AuthState.authenticated(String this.username)
      : status = AuthStatus.authenticated;

  bool get isAuthenticated => status == AuthStatus.authenticated;
}

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(apiClientProvider)),
);

/// 认证状态管理：登录 / 注册 / 登出 / 启动时自动恢复登录态。
final authStateProvider = NotifierProvider<AuthNotifier, AuthState>(
  AuthNotifier.new,
);

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    final store = ref.watch(tokenStoreProvider);
    if (store.isLoggedIn) {
      return AuthState.authenticated(store.username ?? '');
    }
    return const AuthState.unauthenticated();
  }

  Future<void> login(String username, String password) async {
    final session = await ref.read(authRepositoryProvider).login(username, password);
    await ref.read(tokenStoreProvider).save(
          token: session.token,
          userId: session.userId,
          username: session.username,
        );
    state = AuthState.authenticated(session.username);
  }

  Future<void> register(String username, String password) async {
    await ref.read(authRepositoryProvider).register(username, password);
  }

  Future<void> logout() async {
    await ref.read(tokenStoreProvider).clear();
    state = const AuthState.unauthenticated();
  }
}
