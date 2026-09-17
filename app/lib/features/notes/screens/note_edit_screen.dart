import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/l10n/l10n.dart';
import '../../../core/router/app_router.dart';
import '../../../core/widgets/markdown_view.dart';
import '../../agent/agent_provider.dart';
import '../note_model.dart';
import '../note_provider.dart';

/// 笔记编辑/新建页。noteId 为空 = 新建。
class NoteEditScreen extends ConsumerStatefulWidget {
  final String? noteId;
  const NoteEditScreen({super.key, this.noteId});

  @override
  ConsumerState<NoteEditScreen> createState() => _NoteEditScreenState();
}

class _NoteEditScreenState extends ConsumerState<NoteEditScreen> {
  final _title = TextEditingController();
  final _content = TextEditingController();
  bool _preview = false;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final id = widget.noteId;
    if (id == null) return;
    // 优先从已加载的列表取；列表未加载时直接查单条
    Note? found;
    final notes = ref.read(notesProvider).valueOrNull;
    if (notes != null) {
      for (final n in notes) {
        if (n.id == id) {
          found = n;
          break;
        }
      }
    }
    if (found == null) {
      try {
        found = await ref.read(noteRepositoryProvider).get(id);
      } catch (_) {}
    }
    final n = found;
    if (n != null && mounted) {
      setState(() {
        _title.text = n.title;
        _content.text = n.content;
      });
    }
  }

  @override
  void dispose() {
    _title.dispose();
    _content.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final title = _title.text.trim();
    final content = _content.text.trim();
    if (title.isEmpty || content.isEmpty) {
      _snack(context.l10n.titleAndContentRequired);
      return;
    }
    setState(() => _saving = true);
    try {
      final notifier = ref.read(notesProvider.notifier);
      if (widget.noteId == null) {
        await notifier.createNote(title, content);
      } else {
        await notifier.updateNote(widget.noteId!, title: title, content: content);
      }
      if (mounted) context.pop();
    } catch (e) {
      _snack(e.toString());
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _snack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.noteId == null
            ? context.l10n.newNote
            : context.l10n.editNote),
        actions: [
          IconButton(
            icon: Icon(_preview ? Icons.edit_document : Icons.remove_red_eye),
            tooltip: _preview
                ? context.l10n.backToEditing
                : context.l10n.markdownPreview,
            onPressed: () => setState(() => _preview = !_preview),
          ),
          IconButton(
            icon: const Icon(Icons.auto_awesome),
            tooltip: context.l10n.aiAssistantTooltip,
            onPressed: () {
              // 带着「围绕当前笔记复习」的上下文切换到 AI 助手页
              final title = _title.text.trim();
              final l10n = context.l10n;
              ref.read(agentDraftGoalProvider.notifier).state = title.isEmpty
                  ? l10n.reviewCurrentNote
                  : l10n.reviewNoteGoal(title);
              context.go(AppRoutes.agent);
            },
          ),
          _saving
              ? const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Center(
                      child: SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2))),
                )
              : IconButton(
                  icon: const Icon(Icons.check),
                  tooltip: context.l10n.save,
                  onPressed: _save,
                ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _title,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                  hintText: context.l10n.noteTitleHint,
                  border: InputBorder.none),
            ),
            const Divider(height: 16),
            Expanded(
              child: _preview
                  ? MarkdownView(data: _content.text)
                  : TextField(
                      controller: _content,
                      maxLines: null,
                      expands: true,
                      textAlignVertical: TextAlignVertical.top,
                      style: TextStyle(color: scheme.onSurface, height: 1.6),
                      decoration: InputDecoration(
                          hintText: context.l10n.noteContentHint,
                          border: InputBorder.none),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}