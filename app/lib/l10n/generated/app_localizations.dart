import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_zh.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('zh'),
    Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hans'),
  ];

  /// No description provided for @loginSubtitle.
  ///
  /// In en, this message translates to:
  /// **'KnowWeave · your AI study assistant'**
  String get loginSubtitle;

  /// No description provided for @usernameLabel.
  ///
  /// In en, this message translates to:
  /// **'Username'**
  String get usernameLabel;

  /// No description provided for @passwordLabel.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get passwordLabel;

  /// No description provided for @loginButton.
  ///
  /// In en, this message translates to:
  /// **'Log in'**
  String get loginButton;

  /// No description provided for @noAccountRegister.
  ///
  /// In en, this message translates to:
  /// **'No account? Create one'**
  String get noAccountRegister;

  /// No description provided for @loginMissingFields.
  ///
  /// In en, this message translates to:
  /// **'Enter your username and password'**
  String get loginMissingFields;

  /// No description provided for @registerTitle.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get registerTitle;

  /// No description provided for @passwordMinLabel.
  ///
  /// In en, this message translates to:
  /// **'Password (at least 8 characters)'**
  String get passwordMinLabel;

  /// No description provided for @confirmPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'Confirm password'**
  String get confirmPasswordLabel;

  /// No description provided for @registerButton.
  ///
  /// In en, this message translates to:
  /// **'Sign up'**
  String get registerButton;

  /// No description provided for @usernameTooShort.
  ///
  /// In en, this message translates to:
  /// **'Username must be at least 3 characters'**
  String get usernameTooShort;

  /// No description provided for @passwordTooShort.
  ///
  /// In en, this message translates to:
  /// **'Password must be at least 8 characters'**
  String get passwordTooShort;

  /// No description provided for @passwordMismatch.
  ///
  /// In en, this message translates to:
  /// **'The passwords do not match'**
  String get passwordMismatch;

  /// No description provided for @registerSuccess.
  ///
  /// In en, this message translates to:
  /// **'Account created. Please sign in.'**
  String get registerSuccess;

  /// No description provided for @notesTitle.
  ///
  /// In en, this message translates to:
  /// **'My notes'**
  String get notesTitle;

  /// No description provided for @importFile.
  ///
  /// In en, this message translates to:
  /// **'Import file'**
  String get importFile;

  /// No description provided for @importSuccess.
  ///
  /// In en, this message translates to:
  /// **'Imported (ID: {id})'**
  String importSuccess(String id);

  /// No description provided for @importFailed.
  ///
  /// In en, this message translates to:
  /// **'Import failed: {error}'**
  String importFailed(String error);

  /// No description provided for @loadingNotes.
  ///
  /// In en, this message translates to:
  /// **'Loading notes…'**
  String get loadingNotes;

  /// No description provided for @emptyNotes.
  ///
  /// In en, this message translates to:
  /// **'No notes yet'**
  String get emptyNotes;

  /// No description provided for @emptyNotesHint.
  ///
  /// In en, this message translates to:
  /// **'Create one with the button below, or import a PDF, PPTX, or Markdown file'**
  String get emptyNotesHint;

  /// No description provided for @newNote.
  ///
  /// In en, this message translates to:
  /// **'New note'**
  String get newNote;

  /// No description provided for @editNote.
  ///
  /// In en, this message translates to:
  /// **'Edit note'**
  String get editNote;

  /// No description provided for @backToEditing.
  ///
  /// In en, this message translates to:
  /// **'Back to editing'**
  String get backToEditing;

  /// No description provided for @markdownPreview.
  ///
  /// In en, this message translates to:
  /// **'Markdown preview'**
  String get markdownPreview;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @noteTitleHint.
  ///
  /// In en, this message translates to:
  /// **'Note title'**
  String get noteTitleHint;

  /// No description provided for @noteContentHint.
  ///
  /// In en, this message translates to:
  /// **'Start writing in Markdown…'**
  String get noteContentHint;

  /// No description provided for @titleAndContentRequired.
  ///
  /// In en, this message translates to:
  /// **'Title and content cannot be empty'**
  String get titleAndContentRequired;

  /// No description provided for @aiAssistantTooltip.
  ///
  /// In en, this message translates to:
  /// **'AI study assistant'**
  String get aiAssistantTooltip;

  /// No description provided for @reviewCurrentNote.
  ///
  /// In en, this message translates to:
  /// **'Help me revise this note'**
  String get reviewCurrentNote;

  /// No description provided for @reviewNoteGoal.
  ///
  /// In en, this message translates to:
  /// **'Help me revise the note \"{title}\": search it first, summarize it, and quiz me on the key points.'**
  String reviewNoteGoal(String title);

  /// No description provided for @agentTitle.
  ///
  /// In en, this message translates to:
  /// **'AI study assistant'**
  String get agentTitle;

  /// No description provided for @historyMenu.
  ///
  /// In en, this message translates to:
  /// **'Past sessions'**
  String get historyMenu;

  /// No description provided for @agentWelcomeTitle.
  ///
  /// In en, this message translates to:
  /// **'Enter a study goal'**
  String get agentWelcomeTitle;

  /// No description provided for @agentWelcomeExample.
  ///
  /// In en, this message translates to:
  /// **'For example: \"Help me revise chapter three of my operating systems notes\"'**
  String get agentWelcomeExample;

  /// No description provided for @agentWelcomeHint.
  ///
  /// In en, this message translates to:
  /// **'The agent plans on its own: search notes, summarize, quiz, explain concepts'**
  String get agentWelcomeHint;

  /// No description provided for @agentInputHint.
  ///
  /// In en, this message translates to:
  /// **'Enter a goal or a question…'**
  String get agentInputHint;

  /// No description provided for @send.
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get send;

  /// No description provided for @thinkingInProgress.
  ///
  /// In en, this message translates to:
  /// **'Thinking…'**
  String get thinkingInProgress;

  /// No description provided for @thinkingTitle.
  ///
  /// In en, this message translates to:
  /// **'Reasoning'**
  String get thinkingTitle;

  /// No description provided for @thinkingStepCount.
  ///
  /// In en, this message translates to:
  /// **'{count} steps'**
  String thinkingStepCount(int count);

  /// No description provided for @toolCalled.
  ///
  /// In en, this message translates to:
  /// **'Called {tool}'**
  String toolCalled(String tool);

  /// No description provided for @toolFailedSuffix.
  ///
  /// In en, this message translates to:
  /// **' (failed)'**
  String get toolFailedSuffix;

  /// No description provided for @toolCallSummary.
  ///
  /// In en, this message translates to:
  /// **'Called {tool} · {summary}'**
  String toolCallSummary(String tool, String summary);

  /// No description provided for @quizGenerated.
  ///
  /// In en, this message translates to:
  /// **'{count} questions generated'**
  String quizGenerated(int count);

  /// No description provided for @quizFromHistory.
  ///
  /// In en, this message translates to:
  /// **'{count} questions from an earlier session'**
  String quizFromHistory(int count);

  /// No description provided for @errorSend.
  ///
  /// In en, this message translates to:
  /// **'Request failed: {error}'**
  String errorSend(String error);

  /// No description provided for @errorLoadHistory.
  ///
  /// In en, this message translates to:
  /// **'Could not load past sessions: {error}'**
  String errorLoadHistory(String error);

  /// No description provided for @errorSubmitAnswers.
  ///
  /// In en, this message translates to:
  /// **'Could not submit your answers: {error}'**
  String errorSubmitAnswers(String error);

  /// No description provided for @quizResultTitle.
  ///
  /// In en, this message translates to:
  /// **'Result'**
  String get quizResultTitle;

  /// No description provided for @quizScore.
  ///
  /// In en, this message translates to:
  /// **'{correct}/{total}'**
  String quizScore(int correct, int total);

  /// No description provided for @masteryLevel.
  ///
  /// In en, this message translates to:
  /// **'Mastery: {percent}%'**
  String masteryLevel(int percent);

  /// No description provided for @weakPoints.
  ///
  /// In en, this message translates to:
  /// **'Weak points: {points}'**
  String weakPoints(String points);

  /// No description provided for @listSeparator.
  ///
  /// In en, this message translates to:
  /// **', '**
  String get listSeparator;

  /// No description provided for @questionProgress.
  ///
  /// In en, this message translates to:
  /// **'Question {index} of {total}'**
  String questionProgress(int index, int total);

  /// No description provided for @submitAnswers.
  ///
  /// In en, this message translates to:
  /// **'Submit answers'**
  String get submitAnswers;

  /// No description provided for @nextQuestion.
  ///
  /// In en, this message translates to:
  /// **'Next'**
  String get nextQuestion;

  /// No description provided for @navNotes.
  ///
  /// In en, this message translates to:
  /// **'Notes'**
  String get navNotes;

  /// No description provided for @navAgent.
  ///
  /// In en, this message translates to:
  /// **'Assistant'**
  String get navAgent;

  /// No description provided for @navProfile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get navProfile;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @tapToRetry.
  ///
  /// In en, this message translates to:
  /// **'Tap to retry'**
  String get tapToRetry;

  /// No description provided for @requestFailed.
  ///
  /// In en, this message translates to:
  /// **'Request failed (HTTP {status})'**
  String requestFailed(int status);

  /// No description provided for @profileTitle.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profileTitle;

  /// No description provided for @notSignedIn.
  ///
  /// In en, this message translates to:
  /// **'Not signed in'**
  String get notSignedIn;

  /// No description provided for @profileSubtitle.
  ///
  /// In en, this message translates to:
  /// **'KnowWeave · AI-assisted study'**
  String get profileSubtitle;

  /// No description provided for @appearanceSection.
  ///
  /// In en, this message translates to:
  /// **'Appearance'**
  String get appearanceSection;

  /// No description provided for @themeLight.
  ///
  /// In en, this message translates to:
  /// **'Light'**
  String get themeLight;

  /// No description provided for @themeDark.
  ///
  /// In en, this message translates to:
  /// **'Dark'**
  String get themeDark;

  /// No description provided for @themeSystem.
  ///
  /// In en, this message translates to:
  /// **'System'**
  String get themeSystem;

  /// No description provided for @languageSection.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get languageSection;

  /// No description provided for @languageSystem.
  ///
  /// In en, this message translates to:
  /// **'System default'**
  String get languageSystem;

  /// No description provided for @languageEnglish.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get languageEnglish;

  /// No description provided for @languageChineseSimplified.
  ///
  /// In en, this message translates to:
  /// **'简体中文'**
  String get languageChineseSimplified;

  /// No description provided for @aboutSection.
  ///
  /// In en, this message translates to:
  /// **'About'**
  String get aboutSection;

  /// No description provided for @aboutSubtitle.
  ///
  /// In en, this message translates to:
  /// **'KnowWeave · a ReAct agent for studying'**
  String get aboutSubtitle;

  /// No description provided for @signOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get signOut;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'zh'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when language+script codes are specified.
  switch (locale.languageCode) {
    case 'zh':
      {
        switch (locale.scriptCode) {
          case 'Hans':
            return AppLocalizationsZhHans();
        }
        break;
      }
  }

  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'zh':
      return AppLocalizationsZh();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
