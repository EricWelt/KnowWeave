import 'package:flutter_test/flutter_test.dart';

import 'package:know_weave/features/agent/agent_provider.dart';

void main() {
  group('extractQuizFromConversation', () {
    test('从工具返回中提取题目（questions 包装格式）', () {
      final conversation = [
        {
          'role': 'user',
          'content':
              '[工具 create_quiz 返回]\n{"questions": [{"question": "q1", "options": ["A. x", "B. y"], "answer": "A. x", "explanation": "e1"}]}'
        },
      ];
      final quiz = extractQuizFromConversation(conversation);
      expect(quiz, isNotNull);
      expect(quiz!.length, 1);
      expect(quiz[0].question, 'q1');
      expect(quiz[0].options, ['A. x', 'B. y']);
    });

    test('兼容旧格式：顶层数组', () {
      final conversation = [
        {
          'role': 'user',
          'content': '[工具 create_quiz 返回]\n[{"question": "q1", "options": ["A"], "answer": "A", "explanation": "e"}]'
        },
      ];
      final quiz = extractQuizFromConversation(conversation);
      expect(quiz, isNotNull);
      expect(quiz!.length, 1);
    });

    test('非 create_quiz 消息不提取', () {
      final conversation = [
        {
          'role': 'user',
          'content': '[工具 search_notes 返回]\n{"results": []}'
        },
      ];
      expect(extractQuizFromConversation(conversation), isNull);
    });

    test('assistant 消息不提取', () {
      final conversation = [
        {'role': 'assistant', 'content': '工具 create_quiz 返回了题目'},
      ];
      expect(extractQuizFromConversation(conversation), isNull);
    });

    test('无题目时返回 null', () {
      final conversation = [
        {'role': 'user', 'content': '[工具 create_quiz 返回]\n{"questions": []}'},
      ];
      expect(extractQuizFromConversation(conversation), isNull);
    });
  });
}
