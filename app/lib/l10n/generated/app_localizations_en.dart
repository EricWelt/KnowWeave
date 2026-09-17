// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get loginSubtitle => 'KnowWeave · your AI study assistant';

  @override
  String get usernameLabel => 'Username';

  @override
  String get passwordLabel => 'Password';

  @override
  String get loginButton => 'Log in';

  @override
  String get noAccountRegister => 'No account? Create one';

  @override
  String get loginMissingFields => 'Enter your username and password';

  @override
  String get registerTitle => 'Create account';

  @override
  String get passwordMinLabel => 'Password (at least 8 characters)';

  @override
  String get confirmPasswordLabel => 'Confirm password';

  @override
  String get registerButton => 'Sign up';

  @override
  String get usernameTooShort => 'Username must be at least 3 characters';

  @override
  String get passwordTooShort => 'Password must be at least 8 characters';

  @override
  String get passwordMismatch => 'The passwords do not match';

  @override
  String get registerSuccess => 'Account created. Please sign in.';

  @override
  String get notesTitle => 'My notes';

  @override
  String get importFile => 'Import file';

  @override
  String importSuccess(String id) {
    return 'Imported (ID: $id)';
  }

  @override
  String importFailed(String error) {
    return 'Import failed: $error';
  }

  @override
  String get loadingNotes => 'Loading notes…';

  @override
  String get emptyNotes => 'No notes yet';

  @override
  String get emptyNotesHint =>
      'Create one with the button below, or import a PDF, PPTX, or Markdown file';

  @override
  String get newNote => 'New note';

  @override
  String get editNote => 'Edit note';

  @override
  String get backToEditing => 'Back to editing';

  @override
  String get markdownPreview => 'Markdown preview';

  @override
  String get save => 'Save';

  @override
  String get noteTitleHint => 'Note title';

  @override
  String get noteContentHint => 'Start writing in Markdown…';

  @override
  String get titleAndContentRequired => 'Title and content cannot be empty';

  @override
  String get aiAssistantTooltip => 'AI study assistant';

  @override
  String get reviewCurrentNote => 'Help me revise this note';

  @override
  String reviewNoteGoal(String title) {
    return 'Help me revise the note \"$title\": search it first, summarize it, and quiz me on the key points.';
  }

  @override
  String get agentTitle => 'AI study assistant';

  @override
  String get historyMenu => 'Past sessions';

  @override
  String get agentWelcomeTitle => 'Enter a study goal';

  @override
  String get agentWelcomeExample =>
      'For example: \"Help me revise chapter three of my operating systems notes\"';

  @override
  String get agentWelcomeHint =>
      'The agent plans on its own: search notes, summarize, quiz, explain concepts';

  @override
  String get agentInputHint => 'Enter a goal or a question…';

  @override
  String get send => 'Send';

  @override
  String get thinkingInProgress => 'Thinking…';

  @override
  String get thinkingTitle => 'Reasoning';

  @override
  String thinkingStepCount(int count) {
    return '$count steps';
  }

  @override
  String toolCalled(String tool) {
    return 'Called $tool';
  }

  @override
  String get toolFailedSuffix => ' (failed)';

  @override
  String toolCallSummary(String tool, String summary) {
    return 'Called $tool · $summary';
  }

  @override
  String errorSend(String error) {
    return 'Request failed: $error';
  }

  @override
  String errorLoadHistory(String error) {
    return 'Could not load past sessions: $error';
  }

  @override
  String errorSubmitAnswers(String error) {
    return 'Could not submit your answers: $error';
  }

  @override
  String get quizResultTitle => 'Result';

  @override
  String quizScore(int correct, int total) {
    return '$correct/$total';
  }

  @override
  String masteryLevel(int percent) {
    return 'Mastery: $percent%';
  }

  @override
  String weakPoints(String points) {
    return 'Weak points: $points';
  }

  @override
  String get listSeparator => ', ';

  @override
  String questionProgress(int index, int total) {
    return 'Question $index of $total';
  }

  @override
  String get submitAnswers => 'Submit answers';

  @override
  String get nextQuestion => 'Next';

  @override
  String get navNotes => 'Notes';

  @override
  String get navAgent => 'Assistant';

  @override
  String get navProfile => 'Profile';

  @override
  String get retry => 'Retry';

  @override
  String get tapToRetry => 'Tap to retry';

  @override
  String requestFailed(int status) {
    return 'Request failed (HTTP $status)';
  }

  @override
  String get profileTitle => 'Profile';

  @override
  String get notSignedIn => 'Not signed in';

  @override
  String get profileSubtitle => 'KnowWeave · AI-assisted study';

  @override
  String get appearanceSection => 'Appearance';

  @override
  String get themeLight => 'Light';

  @override
  String get themeDark => 'Dark';

  @override
  String get themeSystem => 'System';

  @override
  String get languageSection => 'Language';

  @override
  String get languageSystem => 'System default';

  @override
  String get languageEnglish => 'English';

  @override
  String get languageChineseSimplified => '简体中文';

  @override
  String get aboutSection => 'About';

  @override
  String get aboutSubtitle => 'KnowWeave · a ReAct agent for studying';

  @override
  String get signOut => 'Sign out';

  @override
  String get toolLabel => 'tool';
}
