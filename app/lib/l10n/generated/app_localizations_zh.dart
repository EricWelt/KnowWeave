// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Chinese (`zh`).
class AppLocalizationsZh extends AppLocalizations {
  AppLocalizationsZh([String locale = 'zh']) : super(locale);

  @override
  String get loginSubtitle => '知脉笔记 · 你的智能学习助手';

  @override
  String get usernameLabel => '用户名';

  @override
  String get passwordLabel => '密码';

  @override
  String get loginButton => '登 录';

  @override
  String get noAccountRegister => '没有账号？点击注册';

  @override
  String get loginMissingFields => '请输入用户名和密码';

  @override
  String get registerTitle => '注册新账号';

  @override
  String get passwordMinLabel => '密码（至少 8 位）';

  @override
  String get confirmPasswordLabel => '确认密码';

  @override
  String get registerButton => '注 册';

  @override
  String get usernameTooShort => '用户名至少 3 个字符';

  @override
  String get passwordTooShort => '密码至少 8 个字符';

  @override
  String get passwordMismatch => '两次输入的密码不一致';

  @override
  String get registerSuccess => '注册成功，请登录';

  @override
  String get notesTitle => '我的笔记';

  @override
  String get importFile => '导入文件';

  @override
  String importSuccess(String id) {
    return '导入成功 (ID: $id)';
  }

  @override
  String importFailed(String error) {
    return '导入失败：$error';
  }

  @override
  String get loadingNotes => '加载笔记中…';

  @override
  String get emptyNotes => '还没有笔记';

  @override
  String get emptyNotesHint => '点击右下角创建，或右上角导入 PDF/PPTX/Markdown';

  @override
  String get newNote => '新建笔记';

  @override
  String get editNote => '编辑笔记';

  @override
  String get backToEditing => '返回编辑';

  @override
  String get markdownPreview => 'Markdown 预览';

  @override
  String get save => '保存';

  @override
  String get noteTitleHint => '笔记标题';

  @override
  String get noteContentHint => '开始编写 Markdown…';

  @override
  String get titleAndContentRequired => '标题和内容不能为空';

  @override
  String get aiAssistantTooltip => 'AI 学习助手';

  @override
  String get reviewCurrentNote => '围绕当前笔记帮我复习';

  @override
  String reviewNoteGoal(String title) {
    return '围绕笔记《$title》帮我复习：请先检索这篇笔记，生成摘要，并针对关键知识点出题检验掌握程度。';
  }

  @override
  String get agentTitle => 'AI 学习助手';

  @override
  String get historyMenu => '历史会话';

  @override
  String get agentWelcomeTitle => '输入你的学习目标';

  @override
  String get agentWelcomeExample => '例如：“帮我复习操作系统第三章”';

  @override
  String get agentWelcomeHint => 'Agent 会自主规划：检索笔记 → 生成摘要 → 出题 → 解释概念';

  @override
  String get agentInputHint => '输入学习目标或问题…';

  @override
  String get send => '发送';

  @override
  String get thinkingInProgress => 'AI 思考中…';

  @override
  String get thinkingTitle => '思考过程';

  @override
  String thinkingStepCount(int count) {
    return '$count 个推理步骤';
  }

  @override
  String toolCalled(String tool) {
    return '调用工具 $tool';
  }

  @override
  String get toolFailedSuffix => '（失败）';

  @override
  String errorSend(String error) {
    return '调用失败：$error';
  }

  @override
  String errorLoadHistory(String error) {
    return '加载历史失败：$error';
  }

  @override
  String errorSubmitAnswers(String error) {
    return '提交作答失败：$error';
  }

  @override
  String get quizResultTitle => '答题结果';

  @override
  String quizScore(int correct, int total) {
    return '$correct/$total';
  }

  @override
  String masteryLevel(int percent) {
    return '主题掌握度：$percent%';
  }

  @override
  String weakPoints(String points) {
    return '薄弱点：$points';
  }

  @override
  String get listSeparator => '、';

  @override
  String questionProgress(int index, int total) {
    return '练习题 $index/$total';
  }

  @override
  String get submitAnswers => '提交作答';

  @override
  String get nextQuestion => '下一题';

  @override
  String get navNotes => '笔记';

  @override
  String get navAgent => 'AI 助手';

  @override
  String get navProfile => '我的';

  @override
  String get retry => '重试';

  @override
  String get tapToRetry => '点击重试';

  @override
  String requestFailed(int status) {
    return '请求失败 (HTTP $status)';
  }

  @override
  String get profileTitle => '我的';

  @override
  String get notSignedIn => '未登录';

  @override
  String get profileSubtitle => '知脉笔记 · AI 智能学习';

  @override
  String get appearanceSection => '外观';

  @override
  String get themeLight => '亮色';

  @override
  String get themeDark => '暗色';

  @override
  String get themeSystem => '跟随系统';

  @override
  String get languageSection => '语言';

  @override
  String get languageSystem => '跟随系统';

  @override
  String get languageEnglish => 'English';

  @override
  String get languageChineseSimplified => '简体中文';

  @override
  String get aboutSection => '关于';

  @override
  String get aboutSubtitle => 'KnowWeave · 自研 ReAct Agent 学习系统';

  @override
  String get signOut => '退出登录';

  @override
  String get toolLabel => '工具';
}

/// The translations for Chinese, using the Han script (`zh_Hans`).
class AppLocalizationsZhHans extends AppLocalizationsZh {
  AppLocalizationsZhHans() : super('zh_Hans');

  @override
  String get loginSubtitle => '知脉笔记 · 你的智能学习助手';

  @override
  String get usernameLabel => '用户名';

  @override
  String get passwordLabel => '密码';

  @override
  String get loginButton => '登 录';

  @override
  String get noAccountRegister => '没有账号？点击注册';

  @override
  String get loginMissingFields => '请输入用户名和密码';

  @override
  String get registerTitle => '注册新账号';

  @override
  String get passwordMinLabel => '密码（至少 8 位）';

  @override
  String get confirmPasswordLabel => '确认密码';

  @override
  String get registerButton => '注 册';

  @override
  String get usernameTooShort => '用户名至少 3 个字符';

  @override
  String get passwordTooShort => '密码至少 8 个字符';

  @override
  String get passwordMismatch => '两次输入的密码不一致';

  @override
  String get registerSuccess => '注册成功，请登录';

  @override
  String get notesTitle => '我的笔记';

  @override
  String get importFile => '导入文件';

  @override
  String importSuccess(String id) {
    return '导入成功 (ID: $id)';
  }

  @override
  String importFailed(String error) {
    return '导入失败：$error';
  }

  @override
  String get loadingNotes => '加载笔记中…';

  @override
  String get emptyNotes => '还没有笔记';

  @override
  String get emptyNotesHint => '点击右下角创建，或右上角导入 PDF/PPTX/Markdown';

  @override
  String get newNote => '新建笔记';

  @override
  String get editNote => '编辑笔记';

  @override
  String get backToEditing => '返回编辑';

  @override
  String get markdownPreview => 'Markdown 预览';

  @override
  String get save => '保存';

  @override
  String get noteTitleHint => '笔记标题';

  @override
  String get noteContentHint => '开始编写 Markdown…';

  @override
  String get titleAndContentRequired => '标题和内容不能为空';

  @override
  String get aiAssistantTooltip => 'AI 学习助手';

  @override
  String get reviewCurrentNote => '围绕当前笔记帮我复习';

  @override
  String reviewNoteGoal(String title) {
    return '围绕笔记《$title》帮我复习：请先检索这篇笔记，生成摘要，并针对关键知识点出题检验掌握程度。';
  }

  @override
  String get agentTitle => 'AI 学习助手';

  @override
  String get historyMenu => '历史会话';

  @override
  String get agentWelcomeTitle => '输入你的学习目标';

  @override
  String get agentWelcomeExample => '例如：“帮我复习操作系统第三章”';

  @override
  String get agentWelcomeHint => 'Agent 会自主规划：检索笔记 → 生成摘要 → 出题 → 解释概念';

  @override
  String get agentInputHint => '输入学习目标或问题…';

  @override
  String get send => '发送';

  @override
  String get thinkingInProgress => 'AI 思考中…';

  @override
  String get thinkingTitle => '思考过程';

  @override
  String thinkingStepCount(int count) {
    return '$count 个推理步骤';
  }

  @override
  String toolCalled(String tool) {
    return '调用工具 $tool';
  }

  @override
  String get toolFailedSuffix => '（失败）';

  @override
  String errorSend(String error) {
    return '调用失败：$error';
  }

  @override
  String errorLoadHistory(String error) {
    return '加载历史失败：$error';
  }

  @override
  String errorSubmitAnswers(String error) {
    return '提交作答失败：$error';
  }

  @override
  String get quizResultTitle => '答题结果';

  @override
  String quizScore(int correct, int total) {
    return '$correct/$total';
  }

  @override
  String masteryLevel(int percent) {
    return '主题掌握度：$percent%';
  }

  @override
  String weakPoints(String points) {
    return '薄弱点：$points';
  }

  @override
  String get listSeparator => '、';

  @override
  String questionProgress(int index, int total) {
    return '练习题 $index/$total';
  }

  @override
  String get submitAnswers => '提交作答';

  @override
  String get nextQuestion => '下一题';

  @override
  String get navNotes => '笔记';

  @override
  String get navAgent => 'AI 助手';

  @override
  String get navProfile => '我的';

  @override
  String get retry => '重试';

  @override
  String get tapToRetry => '点击重试';

  @override
  String requestFailed(int status) {
    return '请求失败 (HTTP $status)';
  }

  @override
  String get profileTitle => '我的';

  @override
  String get notSignedIn => '未登录';

  @override
  String get profileSubtitle => '知脉笔记 · AI 智能学习';

  @override
  String get appearanceSection => '外观';

  @override
  String get themeLight => '亮色';

  @override
  String get themeDark => '暗色';

  @override
  String get themeSystem => '跟随系统';

  @override
  String get languageSection => '语言';

  @override
  String get languageSystem => '跟随系统';

  @override
  String get languageEnglish => 'English';

  @override
  String get languageChineseSimplified => '简体中文';

  @override
  String get aboutSection => '关于';

  @override
  String get aboutSubtitle => 'KnowWeave · 自研 ReAct Agent 学习系统';

  @override
  String get signOut => '退出登录';

  @override
  String get toolLabel => '工具';
}
