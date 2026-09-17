import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/l10n.dart';
import '../../../core/router/app_router.dart';
import '../../../core/widgets/glass.dart';
import '../../../core/widgets/status_views.dart';
import '../note_model.dart';
import '../note_provider.dart';

class NoteListScreen extends ConsumerWidget {
  const NoteListScreen({super.key});

  Future<void> _pickAndUpload(BuildContext context, WidgetRef ref) async {
    final messenger = ScaffoldMessenger.of(context);
    final l10n = context.l10n;
    try {
      final result = await FilePicker.platform.pickFiles(
        allowedExtensions: ['pdf', 'pptx', 'md'],
        type: FileType.custom,
      );
      if (result == null || result.files.isEmpty) return;
      final file = result.files.first;
      final noteId =
          await ref.read(notesProvider.notifier).uploadFile(file.path!, file.name);
      messenger.showSnackBar(
          SnackBar(content: Text(l10n.importSuccess(noteId))));
    } catch (e) {
      messenger.showSnackBar(
          SnackBar(content: Text(l10n.importFailed('$e'))));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notes = ref.watch(notesProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.notesTitle),
        actions: [
          // 导入文件（笔记域操作，留在笔记页）
          IconButton(
            icon: const Icon(Icons.upload_file_outlined),
            tooltip: context.l10n.importFile,
            onPressed: () => _pickAndUpload(context, ref),
          ),
        ],
        flexibleSpace: Glass.appBarBackground(context),
      ),
      body: notes.when(
        loading: () => LoadingView(label: context.l10n.loadingNotes),
        error: (e, _) => ErrorView(
          message: describeApiError(context, e),
          onRetry: () => ref.read(notesProvider.notifier).reload(),
        ),
        data: (list) => list.isEmpty
            ? EmptyView(
                icon: Icons.note_add_outlined,
                message: context.l10n.emptyNotes,
                hint: context.l10n.emptyNotesHint,
              )
            : RefreshIndicator(
                onRefresh: () => ref.read(notesProvider.notifier).reload(),
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 96),
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 6),
                  itemBuilder: (context, index) {
                    final note = list[index];
                    return _NoteCard(note: note);
                  },
                ),
              ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push(AppRoutes.noteEdit()),
        icon: const Icon(Icons.add),
        label: Text(context.l10n.newNote),
      ),
    );
  }
}

class _NoteCard extends StatelessWidget {
  final Note note;
  const _NoteCard({required this.note});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final title = note.title;
    final content = note.content;
    final sourceType = note.sourceType;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => context.push(AppRoutes.noteEdit(note.id)),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: scheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _iconFor(sourceType),
                  color: scheme.onPrimaryContainer,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 15)),
                    const SizedBox(height: 3),
                    Text(content,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                            fontSize: 13, color: scheme.onSurfaceVariant)),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: scheme.outline),
            ],
          ),
        ),
      ),
    );
  }

  IconData _iconFor(String sourceType) {
    switch (sourceType) {
      case 'pdf':
        return Icons.picture_as_pdf_outlined;
      case 'pptx':
        return Icons.slideshow_outlined;
      case 'markdown':
        return Icons.description_outlined;
      default:
        return Icons.sticky_note_2_outlined;
    }
  }
}