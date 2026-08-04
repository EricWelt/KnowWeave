import '../../core/network/api_client.dart';
import 'note_model.dart';

/// 笔记数据访问层。
class NoteRepository {
  final ApiClient _api;
  NoteRepository(this._api);

  Future<List<Note>> list({String? search}) async {
    final data = await _api.get('/notes', query: search == null ? null : {'search': search});
    return (data as List)
        .map((e) => Note.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  Future<Note> get(String id) async {
    final data = await _api.get('/notes/$id');
    return Note.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<Note> create(String title, String content) async {
    final data = await _api.post('/notes', body: {'title': title, 'content': content});
    return Note.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<Note> update(String id, {String? title, String? content}) async {
    final data = await _api.put('/notes/$id', body: {
      'title': ?title,
      'content': ?content,
    });
    return Note.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<void> delete(String id) async {
    await _api.delete('/notes/$id');
  }

  Future<void> reindex(String id) async {
    await _api.post('/notes/$id/reindex');
  }

  /// 上传文件导入笔记，返回新笔记 id
  Future<String> upload(String filePath, String filename) async {
    final data = await _api.upload('/upload', filePath, filename);
    return (data as Map)['note_id']?.toString() ?? '';
  }
}
