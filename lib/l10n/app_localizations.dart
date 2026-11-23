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

  /// No description provided for @colBank.
  ///
  /// In en, this message translates to:
  /// **'BANK'**
  String get colBank;

  /// No description provided for @colName.
  ///
  /// In en, this message translates to:
  /// **'NAME'**
  String get colName;

  /// No description provided for @colRxFrequency.
  ///
  /// In en, this message translates to:
  /// **'RX FREQUENCY'**
  String get colRxFrequency;

  /// No description provided for @colToneMode.
  ///
  /// In en, this message translates to:
  /// **'TONE MODE'**
  String get colToneMode;

  /// No description provided for @colTxTone.
  ///
  /// In en, this message translates to:
  /// **'TX TONE'**
  String get colTxTone;

  /// No description provided for @colRxTone.
  ///
  /// In en, this message translates to:
  /// **'RX TONE'**
  String get colRxTone;

  /// No description provided for @colDtcs.
  ///
  /// In en, this message translates to:
  /// **'DTCS'**
  String get colDtcs;

  /// No description provided for @colRxDtcs.
  ///
  /// In en, this message translates to:
  /// **'RX DTCS'**
  String get colRxDtcs;

  /// No description provided for @colDtcsPol.
  ///
  /// In en, this message translates to:
  /// **'DTCS POL'**
  String get colDtcsPol;

  /// No description provided for @colDuplex.
  ///
  /// In en, this message translates to:
  /// **'DUPLEX'**
  String get colDuplex;

  /// No description provided for @colOffset.
  ///
  /// In en, this message translates to:
  /// **'OFFSET / TX FREQ'**
  String get colOffset;

  /// No description provided for @colCrossMode.
  ///
  /// In en, this message translates to:
  /// **'CROSS MODE'**
  String get colCrossMode;

  /// No description provided for @colMode.
  ///
  /// In en, this message translates to:
  /// **'MODE'**
  String get colMode;

  /// No description provided for @colStep.
  ///
  /// In en, this message translates to:
  /// **'STEP'**
  String get colStep;

  /// No description provided for @colPower.
  ///
  /// In en, this message translates to:
  /// **'POWER'**
  String get colPower;

  /// No description provided for @colScan.
  ///
  /// In en, this message translates to:
  /// **'SCAN'**
  String get colScan;

  /// No description provided for @colComment.
  ///
  /// In en, this message translates to:
  /// **'COMMENT'**
  String get colComment;

  /// No description provided for @helpNumber.
  ///
  /// In en, this message translates to:
  /// **'Memory channel number or slot stored in the radio.'**
  String get helpNumber;

  /// No description provided for @helpNumberMidland.
  ///
  /// In en, this message translates to:
  /// **'Midland channel number. Repeater rows are labeled RPTR.'**
  String get helpNumberMidland;

  /// No description provided for @helpBank.
  ///
  /// In en, this message translates to:
  /// **'Bank or zone membership reported by the selected radio. A green boundary marks the start of each bank.'**
  String get helpBank;

  /// No description provided for @helpName.
  ///
  /// In en, this message translates to:
  /// **'Channel name stored in the radio memory.'**
  String get helpName;

  /// No description provided for @helpRxFrequency.
  ///
  /// In en, this message translates to:
  /// **'Receive frequency: the frequency the radio listens on.'**
  String get helpRxFrequency;

  /// No description provided for @helpToneMode.
  ///
  /// In en, this message translates to:
  /// **'Receive/transmit squelch mode. Tone is CTCSS, TSQL is tone squelch, DTCS is a digital code, and Cross uses different tones.'**
  String get helpToneMode;

  /// No description provided for @helpTxTone.
  ///
  /// In en, this message translates to:
  /// **'Transmit CTCSS tone in hertz. TSQL uses the same CTCSS tone for transmit and receive.'**
  String get helpTxTone;

  /// No description provided for @helpRxTone.
  ///
  /// In en, this message translates to:
  /// **'Receive CTCSS tone in hertz. Set Tone Mode to TSQL or a matching Cross mode first.'**
  String get helpRxTone;

  /// No description provided for @helpDtcs.
  ///
  /// In en, this message translates to:
  /// **'Transmit DTCS digital squelch code.'**
  String get helpDtcs;

  /// No description provided for @helpRxDtcs.
  ///
  /// In en, this message translates to:
  /// **'Receive DTCS digital squelch code.'**
  String get helpRxDtcs;

  /// No description provided for @helpDtcsPol.
  ///
  /// In en, this message translates to:
  /// **'DTCS polarity: normal or inverted for transmit and receive.'**
  String get helpDtcsPol;

  /// No description provided for @helpDuplex.
  ///
  /// In en, this message translates to:
  /// **'Transmit/receive relationship. Simplex uses one frequency; offsets or split use different transmit frequencies.'**
  String get helpDuplex;

  /// No description provided for @helpOffset.
  ///
  /// In en, this message translates to:
  /// **'Frequency offset, or the independent transmit frequency for split.'**
  String get helpOffset;

  /// No description provided for @helpCrossMode.
  ///
  /// In en, this message translates to:
  /// **'Separate receive and transmit tone/code modes used with Cross.'**
  String get helpCrossMode;

  /// No description provided for @helpMode.
  ///
  /// In en, this message translates to:
  /// **'Voice modulation: FM, narrowband FM, or AM depending on the radio.'**
  String get helpMode;

  /// No description provided for @helpStep.
  ///
  /// In en, this message translates to:
  /// **'Tuning step size in kHz.'**
  String get helpStep;

  /// No description provided for @helpPower.
  ///
  /// In en, this message translates to:
  /// **'Selected transmit power level.'**
  String get helpPower;

  /// No description provided for @helpScan.
  ///
  /// In en, this message translates to:
  /// **'Whether the channel is included in scanning.'**
  String get helpScan;

  /// No description provided for @helpComment.
  ///
  /// In en, this message translates to:
  /// **'Free-form notes stored with the channel when supported.'**
  String get helpComment;

  /// No description provided for @helpExtra.
  ///
  /// In en, this message translates to:
  /// **'Radio-specific channel setting reported by the CHIRP driver.'**
  String get helpExtra;

  /// No description provided for @dragToReorder.
  ///
  /// In en, this message translates to:
  /// **'Drag to reorder column'**
  String get dragToReorder;

  /// No description provided for @editorTitle.
  ///
  /// In en, this message translates to:
  /// **'Channel details'**
  String get editorTitle;

  /// No description provided for @editorSave.
  ///
  /// In en, this message translates to:
  /// **'Save channel'**
  String get editorSave;

  /// No description provided for @editorBulkTitle.
  ///
  /// In en, this message translates to:
  /// **'Edit {count} channels'**
  String editorBulkTitle(int count);

  /// No description provided for @editorBulkSave.
  ///
  /// In en, this message translates to:
  /// **'Update {count}'**
  String editorBulkSave(int count);

  /// No description provided for @tipAbbreviations.
  ///
  /// In en, this message translates to:
  /// **'Abbreviations & terms'**
  String get tipAbbreviations;

  /// No description provided for @tipResetRepeater.
  ///
  /// In en, this message translates to:
  /// **'Reset repeater'**
  String get tipResetRepeater;

  /// No description provided for @tipDeleteChannel.
  ///
  /// In en, this message translates to:
  /// **'Delete channel'**
  String get tipDeleteChannel;

  /// No description provided for @tipCloseEditor.
  ///
  /// In en, this message translates to:
  /// **'Close editor'**
  String get tipCloseEditor;

  /// No description provided for @fieldChannel.
  ///
  /// In en, this message translates to:
  /// **'Channel'**
  String get fieldChannel;

  /// No description provided for @fieldLocation.
  ///
  /// In en, this message translates to:
  /// **'Location'**
  String get fieldLocation;

  /// No description provided for @fieldName.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get fieldName;

  /// No description provided for @fieldReceiveChannel.
  ///
  /// In en, this message translates to:
  /// **'Receive channel'**
  String get fieldReceiveChannel;

  /// No description provided for @fieldReceiveFrequency.
  ///
  /// In en, this message translates to:
  /// **'Receive frequency (MHz)'**
  String get fieldReceiveFrequency;

  /// No description provided for @fieldDuplex.
  ///
  /// In en, this message translates to:
  /// **'Duplex'**
  String get fieldDuplex;

  /// No description provided for @fieldTxFrequency.
  ///
  /// In en, this message translates to:
  /// **'TX frequency'**
  String get fieldTxFrequency;

  /// No description provided for @fieldOffset.
  ///
  /// In en, this message translates to:
  /// **'Offset (MHz)'**
  String get fieldOffset;

  /// No description provided for @fieldToneMode.
  ///
  /// In en, this message translates to:
  /// **'Tone mode'**
  String get fieldToneMode;

  /// No description provided for @fieldCrossMode.
  ///
  /// In en, this message translates to:
  /// **'Cross mode'**
  String get fieldCrossMode;

  /// No description provided for @fieldCtcssTone.
  ///
  /// In en, this message translates to:
  /// **'CTCSS tone (Hz)'**
  String get fieldCtcssTone;

  /// No description provided for @fieldTransmitTone.
  ///
  /// In en, this message translates to:
  /// **'Transmit tone (Hz)'**
  String get fieldTransmitTone;

  /// No description provided for @fieldReceiveTone.
  ///
  /// In en, this message translates to:
  /// **'Receive tone (Hz)'**
  String get fieldReceiveTone;

  /// No description provided for @fieldDtcsCode.
  ///
  /// In en, this message translates to:
  /// **'DTCS code'**
  String get fieldDtcsCode;

  /// No description provided for @fieldTransmitDtcs.
  ///
  /// In en, this message translates to:
  /// **'Transmit DTCS'**
  String get fieldTransmitDtcs;

  /// No description provided for @fieldReceiveDtcs.
  ///
  /// In en, this message translates to:
  /// **'Receive DTCS'**
  String get fieldReceiveDtcs;

  /// No description provided for @fieldDtcsPolarity.
  ///
  /// In en, this message translates to:
  /// **'DTCS polarity (TX / RX)'**
  String get fieldDtcsPolarity;

  /// No description provided for @fieldMode.
  ///
  /// In en, this message translates to:
  /// **'Mode'**
  String get fieldMode;

  /// No description provided for @fieldStep.
  ///
  /// In en, this message translates to:
  /// **'Step (kHz)'**
  String get fieldStep;

  /// No description provided for @fieldScan.
  ///
  /// In en, this message translates to:
  /// **'Scan'**
  String get fieldScan;

  /// No description provided for @fieldTransmitPower.
  ///
  /// In en, this message translates to:
  /// **'Transmit power'**
  String get fieldTransmitPower;

  /// No description provided for @fieldComment.
  ///
  /// In en, this message translates to:
  /// **'Comment'**
  String get fieldComment;

  /// No description provided for @radioSpecificSettings.
  ///
  /// In en, this message translates to:
  /// **'Radio-specific channel settings'**
  String get radioSpecificSettings;

  /// No description provided for @gm32ReceiveOnly.
  ///
  /// In en, this message translates to:
  /// **'This frequency is receive-only. The GM-32 transmits on GMRS channels.'**
  String get gm32ReceiveOnly;

  /// No description provided for @choiceNone.
  ///
  /// In en, this message translates to:
  /// **'None'**
  String get choiceNone;

  /// No description provided for @choiceToneSquelch.
  ///
  /// In en, this message translates to:
  /// **'Tone squelch'**
  String get choiceToneSquelch;

  /// No description provided for @choiceSimplex.
  ///
  /// In en, this message translates to:
  /// **'Simplex'**
  String get choiceSimplex;

  /// No description provided for @choicePlusShift.
  ///
  /// In en, this message translates to:
  /// **'+ shift'**
  String get choicePlusShift;

  /// No description provided for @choiceMinusShift.
  ///
  /// In en, this message translates to:
  /// **'− shift'**
  String get choiceMinusShift;

  /// No description provided for @choiceSplit.
  ///
  /// In en, this message translates to:
  /// **'Split'**
  String get choiceSplit;

  /// No description provided for @choiceTxOff.
  ///
  /// In en, this message translates to:
  /// **'TX off'**
  String get choiceTxOff;

  /// No description provided for @choiceDtcsToNone.
  ///
  /// In en, this message translates to:
  /// **'DTCS → None'**
  String get choiceDtcsToNone;

  /// No description provided for @choiceNoneToDtcs.
  ///
  /// In en, this message translates to:
  /// **'None → DTCS'**
  String get choiceNoneToDtcs;

  /// No description provided for @choiceNoneToTone.
  ///
  /// In en, this message translates to:
  /// **'None → Tone'**
  String get choiceNoneToTone;

  /// No description provided for @choiceNormalNormal.
  ///
  /// In en, this message translates to:
  /// **'Normal / Normal'**
  String get choiceNormalNormal;

  /// No description provided for @choiceNormalReverse.
  ///
  /// In en, this message translates to:
  /// **'Normal / Reverse'**
  String get choiceNormalReverse;

  /// No description provided for @choiceReverseNormal.
  ///
  /// In en, this message translates to:
  /// **'Reverse / Normal'**
  String get choiceReverseNormal;

  /// No description provided for @choiceReverseReverse.
  ///
  /// In en, this message translates to:
  /// **'Reverse / Reverse'**
  String get choiceReverseReverse;

  /// No description provided for @choiceDigitalVoice.
  ///
  /// In en, this message translates to:
  /// **'Digital voice'**
  String get choiceDigitalVoice;
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
