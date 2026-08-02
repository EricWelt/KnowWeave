/// 应用配置。
///
/// 后端地址可通过构建时注入覆盖（真机连 PC 时用局域网 IP）：
///   flutter build apk --dart-define=API_BASE_URL=http://127.0.0.1:8000
class AppConfig {
  AppConfig._();

  static const String appName = 'KnowWeave';

  /// 后端基础地址。默认值为开发机局域网 IP（与手机同一 WiFi 时可访问），
  /// 构建/运行时可经 --dart-define=API_BASE_URL=... 覆盖。
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
}
