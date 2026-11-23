import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';
import 'app_localizations_fr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
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
    Locale('es'),
    Locale('fr'),
  ];

  /// No description provided for @navRadioConnection.
  ///
  /// In en, this message translates to:
  /// **'Radio connection'**
  String get navRadioConnection;

  /// No description provided for @navChannelLibrary.
  ///
  /// In en, this message translates to:
  /// **'Channel library'**
  String get navChannelLibrary;

  /// No description provided for @navRadioSettings.
  ///
  /// In en, this message translates to:
  /// **'Radio settings'**
  String get navRadioSettings;

  /// No description provided for @navFindRepeaters.
  ///
  /// In en, this message translates to:
  /// **'Find repeaters'**
  String get navFindRepeaters;

  /// No description provided for @navFrequencyReference.
  ///
  /// In en, this message translates to:
  /// **'Frequency reference'**
  String get navFrequencyReference;

  /// No description provided for @navAbout.
  ///
  /// In en, this message translates to:
  /// **'About & licenses'**
  String get navAbout;

  /// No description provided for @sidebarDesktopProgrammer.
  ///
  /// In en, this message translates to:
  /// **'DESKTOP RADIO PROGRAMMER'**
  String get sidebarDesktopProgrammer;

  /// No description provided for @sidebarLeadProgrammer.
  ///
  /// In en, this message translates to:
  /// **'Lead Programmer'**
  String get sidebarLeadProgrammer;

  /// No description provided for @sidebarVersion.
  ///
  /// In en, this message translates to:
  /// **'Version {version}'**
  String sidebarVersion(String version);

  /// No description provided for @languageLabel.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get languageLabel;

  /// No description provided for @languageSystem.
  ///
  /// In en, this message translates to:
  /// **'System default'**
  String get languageSystem;

  /// No description provided for @languageBetaNote.
  ///
  /// In en, this message translates to:
  /// **'Translations are in beta. Messages from radio drivers stay in English.'**
  String get languageBetaNote;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @ok.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get ok;

  /// No description provided for @apply.
  ///
  /// In en, this message translates to:
  /// **'Apply'**
  String get apply;

  /// No description provided for @readReplaceTitle.
  ///
  /// In en, this message translates to:
  /// **'Replace current channel list?'**
  String get readReplaceTitle;

  /// No description provided for @readReplaceBody.
  ///
  /// In en, this message translates to:
  /// **'Reading channels from the radio will replace the current channel list. Save it as a CSV first if you want to keep it.'**
  String get readReplaceBody;

  /// No description provided for @readChannels.
  ///
  /// In en, this message translates to:
  /// **'Read channels'**
  String get readChannels;

  /// No description provided for @radioReadyToReceive.
  ///
  /// In en, this message translates to:
  /// **'Radio is ready to receive'**
  String get radioReadyToReceive;

  /// No description provided for @radioReady.
  ///
  /// In en, this message translates to:
  /// **'Radio is ready'**
  String get radioReady;

  /// No description provided for @beforeReading.
  ///
  /// In en, this message translates to:
  /// **'Before reading {model}'**
  String beforeReading(String model);

  /// No description provided for @beforeWriting.
  ///
  /// In en, this message translates to:
  /// **'Before writing {model}'**
  String beforeWriting(String model);

  /// No description provided for @readingProgress.
  ///
  /// In en, this message translates to:
  /// **'Reading radio channels - do not disconnect...'**
  String get readingProgress;

  /// No description provided for @writingProgress.
  ///
  /// In en, this message translates to:
  /// **'Writing radio — do not disconnect…'**
  String get writingProgress;

  /// No description provided for @writingSettingsProgress.
  ///
  /// In en, this message translates to:
  /// **'Writing radio settings - do not disconnect...'**
  String get writingSettingsProgress;

  /// No description provided for @writeUnavailableTitle.
  ///
  /// In en, this message translates to:
  /// **'Writing to the {model} isn\'t available yet'**
  String writeUnavailableTitle(String model);

  /// No description provided for @writeUnavailableBody.
  ///
  /// In en, this message translates to:
  /// **'NewChirp can read this radio, but writing stays off until a write has been tested and checked on a real radio. That keeps an untested write from damaging your radio\'s setup.\n\nYou can still read the radio, edit channels, and save or export them. If you can help test writing, send a bug report and say so.'**
  String get writeUnavailableBody;

  /// No description provided for @incompatibleTitle.
  ///
  /// In en, this message translates to:
  /// **'Some channels are incompatible'**
  String get incompatibleTitle;

  /// No description provided for @incompatibleSummary.
  ///
  /// In en, this message translates to:
  /// **'{invalid} of {total} channels cannot be written to this radio.'**
  String incompatibleSummary(int invalid, int total);

  /// No description provided for @incompatibleMore.
  ///
  /// In en, this message translates to:
  /// **'…and {count} more.'**
  String incompatibleMore(int count);

  /// No description provided for @incompatibleSkipHint.
  ///
  /// In en, this message translates to:
  /// **'You can skip the incompatible channels and write the other {count}.'**
  String incompatibleSkipHint(int count);

  /// No description provided for @reviewChannels.
  ///
  /// In en, this message translates to:
  /// **'Review channels'**
  String get reviewChannels;

  /// No description provided for @skipAndWriteRemaining.
  ///
  /// In en, this message translates to:
  /// **'Skip and write remaining'**
  String get skipAndWriteRemaining;

  /// No description provided for @writeChangesTitle.
  ///
  /// In en, this message translates to:
  /// **'Write these radio changes?'**
  String get writeChangesTitle;

  /// No description provided for @writeChannelsTitle.
  ///
  /// In en, this message translates to:
  /// **'Write these channels to the radio?'**
  String get writeChannelsTitle;

  /// No description provided for @writeConfirmBody.
  ///
  /// In en, this message translates to:
  /// **'This will program {count} channels on {model} through {port}. Keep the radio connected and powered on.'**
  String writeConfirmBody(int count, String model, String port);

  /// No description provided for @writeConfirmMappings.
  ///
  /// In en, this message translates to:
  /// **'Bank and zone changes will be written too.'**
  String get writeConfirmMappings;

  /// No description provided for @writeConfirmIncompatible.
  ///
  /// In en, this message translates to:
  /// **'{count} incompatible channels will be left unchanged and listed after the write.'**
  String writeConfirmIncompatible(int count);

  /// No description provided for @writeConfirmUppercase.
  ///
  /// In en, this message translates to:
  /// **'Lowercase channel names will be converted to uppercase because this radio only supports uppercase names.'**
  String get writeConfirmUppercase;

  /// No description provided for @writeToRadio.
  ///
  /// In en, this message translates to:
  /// **'Write to radio'**
  String get writeToRadio;

  /// No description provided for @applyTitle.
  ///
  /// In en, this message translates to:
  /// **'Apply {label}'**
  String applyTitle(String label);

  /// No description provided for @applyIntro.
  ///
  /// In en, this message translates to:
  /// **'Choose how to add these channels to the current list.'**
  String get applyIntro;

  /// No description provided for @applyReplaceList.
  ///
  /// In en, this message translates to:
  /// **'Replace the current channel list'**
  String get applyReplaceList;

  /// No description provided for @applyReplaceZone.
  ///
  /// In en, this message translates to:
  /// **'Replace the channels in zone {zone}'**
  String applyReplaceZone(String zone);

  /// No description provided for @applyReplaceListNote.
  ///
  /// In en, this message translates to:
  /// **'Unsaved edits to the current list will be lost.'**
  String get applyReplaceListNote;

  /// No description provided for @applyReplaceZoneNote.
  ///
  /// In en, this message translates to:
  /// **'Other zones are not changed. Unsaved edits to this zone will be lost.'**
  String get applyReplaceZoneNote;

  /// No description provided for @applyInsertAt.
  ///
  /// In en, this message translates to:
  /// **'Insert starting at channel number'**
  String get applyInsertAt;

  /// No description provided for @applyInsertNote.
  ///
  /// In en, this message translates to:
  /// **'Channels in the {count}-channel range will be overwritten.'**
  String applyInsertNote(int count);

  /// No description provided for @applyStartLabel.
  ///
  /// In en, this message translates to:
  /// **'Starting channel number'**
  String get applyStartLabel;

  /// No description provided for @applyStartError.
  ///
  /// In en, this message translates to:
  /// **'Enter a channel number of 1 or higher.'**
  String get applyStartError;

  /// No description provided for @settingsUnsaved.
  ///
  /// In en, this message translates to:
  /// **'Unsaved settings changes'**
  String get settingsUnsaved;

  /// No description provided for @settingsMatchRadio.
  ///
  /// In en, this message translates to:
  /// **'Settings match the values last read from the radio.'**
  String get settingsMatchRadio;

  /// No description provided for @settingsMatchSnapshot.
  ///
  /// In en, this message translates to:
  /// **'Settings match the saved radio snapshot.'**
  String get settingsMatchSnapshot;

  /// No description provided for @discardChanges.
  ///
  /// In en, this message translates to:
  /// **'Discard changes'**
  String get discardChanges;

  /// No description provided for @connectRadioToWrite.
  ///
  /// In en, this message translates to:
  /// **'Connect radio to write'**
  String get connectRadioToWrite;

  /// No description provided for @writeSettingsToRadio.
  ///
  /// In en, this message translates to:
  /// **'Write settings to radio'**
  String get writeSettingsToRadio;

  /// No description provided for @writeSettingsTitle.
  ///
  /// In en, this message translates to:
  /// **'Write these radio settings?'**
  String get writeSettingsTitle;

  /// No description provided for @writeSameSettingsTitle.
  ///
  /// In en, this message translates to:
  /// **'Write the same settings again?'**
  String get writeSameSettingsTitle;

  /// No description provided for @writeSettingsBody.
  ///
  /// In en, this message translates to:
  /// **'This will write {count} radio setting values to {model} through {port}. Keep the radio connected and powered on.'**
  String writeSettingsBody(int count, String model, String port);

  /// No description provided for @writeSameSettingsBody.
  ///
  /// In en, this message translates to:
  /// **'Nothing has changed since the last read or write. NewChirp will write this radio snapshot, its settings and its channels, to {model} through {port}. Use this to program another radio of the same model. Keep the radio connected and powered on.'**
  String writeSameSettingsBody(String model, String port);

  /// No description provided for @writeSettingsButton.
  ///
  /// In en, this message translates to:
  /// **'Write settings'**
  String get writeSettingsButton;
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
      <String>['en', 'es', 'fr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
    case 'fr':
      return AppLocalizationsFr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
