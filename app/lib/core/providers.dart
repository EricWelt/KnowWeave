import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'network/api_client.dart';
import 'storage/token_store.dart';

/// SharedPreferences 实例（main() 中初始化后注入）
final sharedPreferencesProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError('在 main() 中 override'),
);

final tokenStoreProvider = Provider<TokenStore>(
  (ref) => TokenStore(ref.watch(sharedPreferencesProvider)),
);

final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(
    client: http.Client(),
    tokenStore: ref.watch(tokenStoreProvider),
  ),
);
