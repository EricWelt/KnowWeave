import 'package:flutter/material.dart';

import '../../models/agent_models.dart';

/// 可交互选择题卡片：逐题作答 → 展示解析 → 完成后提交结果。
class QuizCard extends StatefulWidget {
  final List<QuizQuestion> questions;
  final Future<void> Function(List<QuizAnswer> answers) onAnswer;

  const QuizCard({super.key, required this.questions, required this.onAnswer});

  @override
  State<QuizCard> createState() => _QuizCardState();
}

class _QuizCardState extends State<QuizCard> {
  int _index = 0;
  String? _selected;
  bool _revealed = false;
  final List<QuizAnswer> _answers = [];

  QuizQuestion get _q => widget.questions[_index];

  void _select(String option) {
    if (_revealed) return;
    setState(() {
      _selected = option;
      _revealed = true;
    });
  }

  void _next() {
    final isCorrect = _selected == _q.answer;
    _answers.add(QuizAnswer(
      question: _q.question,
      selected: _selected ?? '',
      correct: _q.answer,
      isCorrect: isCorrect,
    ));
    if (_index < widget.questions.length - 1) {
      setState(() {
        _index++;
        _selected = null;
        _revealed = false;
      });
    } else {
      widget.onAnswer(_answers);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.quiz_outlined, color: scheme.primary, size: 20),
                const SizedBox(width: 8),
                Text('练习题 ${_index + 1}/${widget.questions.length}',
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ],
            ),
            const SizedBox(height: 12),
            Text(_q.question,
                style: const TextStyle(fontSize: 15, height: 1.5)),
            const SizedBox(height: 12),
            ..._q.options.map((option) {
              Color? bg;
              if (_revealed) {
                if (option == _q.answer) {
                  bg = Colors.green.shade100;
                } else if (option == _selected) {
                  bg = Colors.red.shade100;
                }
              }
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Material(
                  color: bg ?? scheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(10),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: () => _select(option),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 10),
                      child: Row(
                        children: [
                          Expanded(
                              child: Text(option,
                                  style: const TextStyle(fontSize: 14))),
                          if (_revealed && option == _q.answer)
                            const Icon(Icons.check_circle,
                                color: Colors.green, size: 18),
                          if (_revealed && option == _selected && option != _q.answer)
                            const Icon(Icons.cancel,
                                color: Colors.red, size: 18),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            }),
            if (_revealed) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: scheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text('💡 ${_q.explanation}',
                    style: TextStyle(
                        fontSize: 13, height: 1.5, color: scheme.onSurfaceVariant)),
              ),
              const SizedBox(height: 12),
              Align(
                alignment: Alignment.centerRight,
                child: FilledButton(
                  onPressed: _next,
                  child: Text(_index == widget.questions.length - 1
                      ? '提交作答'
                      : '下一题'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}


