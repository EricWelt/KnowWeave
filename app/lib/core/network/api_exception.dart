/// 统一 API 异常：携带 HTTP 状态码与后端返回的 detail 信息。
class ApiException implements Exception {
  final int? statusCode;
  final String message;

  ApiException(this.message, {this.statusCode});

  /// 未授权（token 失效等）
  bool get isUnauthorized => statusCode == 401;

  @override
  String toString() => message;
}
