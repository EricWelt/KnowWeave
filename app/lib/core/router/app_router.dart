import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/agent/screens/agent_chat_screen.dart';
import '../../features/auth/auth_provider.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/notes/screens/note_edit_screen.dart';
import '../../features/notes/screens/note_list_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../widgets/shell_screen.dart';

/// 路由表（go_router）：
/// - /login /register：认证页
/// - /notes /agent /profile：底栏三页（StatefulShellRoute，切换保留状态）
/// - /notes/edit：笔记编辑（全屏，压在底栏之上）
final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/notes',
    redirect: (context, state) {
      final loggedIn = ref.read(authStateProvider).isAuthenticated;
      final isAuthPage = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';
      if (!loggedIn) {
        return isAuthPage ? null : '/login';
      }
      if (loggedIn && isAuthPage) return '/notes';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (_, _) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        name: 'register',
        builder: (_, _) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/notes/edit',
        name: 'note-edit',
        builder: (_, state) {
          final noteId = state.uri.queryParameters['id'];
          return NoteEditScreen(noteId: noteId);
        },
      ),
      StatefulShellRoute.indexedStack(
        builder: (_, _, navigationShell) =>
            ShellScreen(shell: navigationShell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/notes',
                name: 'notes',
                builder: (_, _) => const NoteListScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/agent',
                name: 'agent',
                builder: (_, _) => const AgentChatScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/profile',
                name: 'profile',
                builder: (_, _) => const ProfileScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
});

/// 路由跳转辅助
class AppRoutes {
  AppRoutes._();
  static const login = '/login';
  static const register = '/register';
  static const notes = '/notes';
  static const agent = '/agent';
  static const profile = '/profile';

  static String noteEdit([String? id]) =>
      id == null ? '/notes/edit' : '/notes/edit?id=$id';
}