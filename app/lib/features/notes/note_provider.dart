import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import 'note_model.dart';
import 'note_repository.dart';

final noteRepositoryProvider = Provider<NoteRepository>(
  (ref) => NoteRepository(ref.watch(apiClientProvider)),
);

/// 笔记列表状态（AsyncNotifier：自动处理 loading/error/data）。
final notesProvider = AsyncNotifierProvider<NotesNotifier, List<Note>>(
  NotesNotifier.new,
);

class NotesNotifier extends AsyncNotifier<List<Note>> {
  NoteRepository get _repo => ref.read(noteRepositoryProvider);

  @override
  Future<List<Note>> build() => _repo.list();

  Future<void> reload() async {
    state = await AsyncValue.guard(_repo.list);
  }

  Future<void> createNote(String title, String content) async {
    await _repo.create(title, content);
    await reload();
  }

  Future<void> updateNote(String id, {String? title, String? content}) async {
    await _repo.update(id, title: title, content: content);
    await reload();
  }

  Future<void> deleteNote(String id) async {
    await _repo.delete(id);
    await reload();
  }

  Future<String> uploadFile(String filePath, String filename) async {
    final noteId = await _repo.upload(filePath, filename);
    await reload();
    return noteId;
  }
}
