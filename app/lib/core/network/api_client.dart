import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../storage/token_store.dart';
import 'api_exception.dart';

/// 统一 HTTP 客户端：
/// - 自动附带 Bearer token
/// - UTF-8 解码（后端中文）
/// - 非 2xx 统一抛 [ApiException]（解析后端 detail 字段）
/// - 注入 [http.Client]，测试时可替换为 MockClient
class ApiClient {
  final http.Client _client;
  final TokenStore _tokenStore;
  final String baseUrl;

  ApiClient({
    required http.Client client,
    required TokenStore tokenStore,
    String? baseUrl,
  })  : _client = client,
        _tokenStore = tokenStore,
        baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  Uri _uri(String path, [Map<String, String>? query]) =>
      Uri.parse('$baseUrl$path').replace(queryParameters: query);

  Map<String, String> _headers({bool json = true}) {
    final h = <String, String>{};
    if (json) h['Content-Type'] = 'application/json';
    final t = _tokenStore.token;
    if (t != null && t.isNotEmpty) h['Authorization'] = 'Bearer $t';
    return h;
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    final resp = await _client.get(_uri(path, query), headers: _headers());
    return _decode(resp);
  }

  Future<dynamic> post(String path, {Object? body}) async {
    final resp = await _client.post(
      _uri(path),
      headers: _headers(),
      body: body == null ? null : jsonEncode(body),
    );
    return _decode(resp);
  }

  Future<dynamic> put(String path, {Object? body}) async {
    final resp = await _client.put(
      _uri(path),
      headers: _headers(),
      body: body == null ? null : jsonEncode(body),
    );
    return _decode(resp);
  }

  Future<dynamic> delete(String path) async {
    final resp = await _client.delete(_uri(path), headers: _headers());
    return _decode(resp);
  }

  /// multipart 上传（文件导入）
  Future<dynamic> upload(String path, String filePath, String filename) async {
    final request = http.MultipartRequest('POST', _uri(path))
      ..headers['Authorization'] = 'Bearer ${_tokenStore.token}'
      ..files.add(await http.MultipartFile.fromPath('file', filePath,
          filename: filename));
    final streamed = await _client.send(request);
    final body = await streamed.stream.bytesToString();
    return _decode(http.Response(body, streamed.statusCode));
  }

  dynamic _decode(http.Response resp) {
    final body = utf8.decode(resp.bodyBytes);
    if (resp.statusCode >= 200 && resp.statusCode < 300) {
      if (body.isEmpty) return null;
      return jsonDecode(body);
    }
    throw ApiException(_extractDetail(body, resp.statusCode),
        statusCode: resp.statusCode);
  }

  String _extractDetail(String body, int statusCode) {
    try {
      final data = jsonDecode(body);
      if (data is Map && data['detail'] != null) return data['detail'].toString();
    } catch (_) {}
    return '请求失败 (HTTP $statusCode)';
  }
}
