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

  /// No description provided for @connIntro.
  ///
  /// In en, this message translates to:
  /// **'Read channels from the radio first, edit them in the library, then write the verified image back.'**
  String get connIntro;

  /// No description provided for @moduleLoaded.
  ///
  /// In en, this message translates to:
  /// **'Experimental CHIRP module loaded: {name}'**
  String moduleLoaded(String name);

  /// No description provided for @unload.
  ///
  /// In en, this message translates to:
  /// **'Unload'**
  String get unload;

  /// No description provided for @step1Title.
  ///
  /// In en, this message translates to:
  /// **'Choose a programming cable'**
  String get step1Title;

  /// No description provided for @step1Help.
  ///
  /// In en, this message translates to:
  /// **'NewChirp finds USB serial and mass-storage programming interfaces automatically. Choose the one that matches your radio connection. If nothing appears, connect the radio and press refresh.'**
  String get step1Help;

  /// No description provided for @programmingInterface.
  ///
  /// In en, this message translates to:
  /// **'Programming interface'**
  String get programmingInterface;

  /// No description provided for @refreshInterfaces.
  ///
  /// In en, this message translates to:
  /// **'Refresh interfaces'**
  String get refreshInterfaces;

  /// No description provided for @refreshHelp.
  ///
  /// In en, this message translates to:
  /// **'Rescan the system for USB serial and mass-storage programming interfaces. If your radio is not listed, connect it and press refresh.'**
  String get refreshHelp;

  /// No description provided for @noInterface.
  ///
  /// In en, this message translates to:
  /// **'No programming interface detected. Connect the radio and choose refresh.'**
  String get noInterface;

  /// No description provided for @step2Title.
  ///
  /// In en, this message translates to:
  /// **'Choose the exact radio model'**
  String get step2Title;

  /// No description provided for @step2Help.
  ///
  /// In en, this message translates to:
  /// **'Load the supported radio catalog and select the exact model. Using the wrong model can corrupt a radio. Programming cables do not identify the attached radio, so NewChirp does not guess the model. If a stored image already exists for this model, writing is unlocked without reading again.'**
  String get step2Help;

  /// No description provided for @loadCatalog.
  ///
  /// In en, this message translates to:
  /// **'Load supported radio catalog'**
  String get loadCatalog;

  /// No description provided for @loadCatalogHelp.
  ///
  /// In en, this message translates to:
  /// **'Fetch the list of radio models supported by the bundled CHIRP driver tree. Select the exact model before reading or writing.'**
  String get loadCatalogHelp;

  /// No description provided for @step3Title.
  ///
  /// In en, this message translates to:
  /// **'Transfer safely'**
  String get step3Title;

  /// No description provided for @step3Help.
  ///
  /// In en, this message translates to:
  /// **'Read channels pulls the full memory image from the radio, replaces the current channel list, and stores the image for this model. Radio settings have a separate read action on the Radio settings page. Write sends the current channel list back using the stored image. Keep the radio connected and powered on during either transfer.'**
  String get step3Help;

  /// No description provided for @readChannelsFromRadio.
  ///
  /// In en, this message translates to:
  /// **'Read channels from radio'**
  String get readChannelsFromRadio;

  /// No description provided for @imageNone.
  ///
  /// In en, this message translates to:
  /// **'No image for this model yet. Read once to enable writing.'**
  String get imageNone;

  /// No description provided for @imageStored.
  ///
  /// In en, this message translates to:
  /// **'Stored image for {model} is ready. You can write without reading again.'**
  String imageStored(String model);

  /// No description provided for @imageSession.
  ///
  /// In en, this message translates to:
  /// **'A radio image was read this session. Review all changes before writing.'**
  String get imageSession;

  /// No description provided for @pickerSemanticsChoose.
  ///
  /// In en, this message translates to:
  /// **'Choose radio model'**
  String get pickerSemanticsChoose;

  /// No description provided for @pickerSemanticsSelected.
  ///
  /// In en, this message translates to:
  /// **'Selected radio {model}'**
  String pickerSemanticsSelected(String model);

  /// No description provided for @pickerLabel.
  ///
  /// In en, this message translates to:
  /// **'Radio model'**
  String get pickerLabel;

  /// No description provided for @pickerHint.
  ///
  /// In en, this message translates to:
  /// **'Choose from {count} supported radios'**
  String pickerHint(int count);

  /// No description provided for @pickerTitle.
  ///
  /// In en, this message translates to:
  /// **'Choose your radio'**
  String get pickerTitle;

  /// No description provided for @pickerSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Browse by manufacturer or search the complete catalog.'**
  String get pickerSubtitle;

  /// No description provided for @close.
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get close;

  /// No description provided for @pickerSearchHint.
  ///
  /// In en, this message translates to:
  /// **'Search by manufacturer or model, e.g. Icom ID-52'**
  String get pickerSearchHint;

  /// No description provided for @clearSearch.
  ///
  /// In en, this message translates to:
  /// **'Clear search'**
  String get clearSearch;

  /// No description provided for @pickerNoMatch.
  ///
  /// In en, this message translates to:
  /// **'No radio models match this search.'**
  String get pickerNoMatch;

  /// No description provided for @pickerCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 radio} other{{count} radios}}'**
  String pickerCount(int count);

  /// No description provided for @pickerAllVendors.
  ///
  /// In en, this message translates to:
  /// **'All manufacturers'**
  String get pickerAllVendors;

  /// No description provided for @pickerRecent.
  ///
  /// In en, this message translates to:
  /// **'Recent'**
  String get pickerRecent;

  /// No description provided for @selected.
  ///
  /// In en, this message translates to:
  /// **'Selected'**
  String get selected;

  /// No description provided for @edited.
  ///
  /// In en, this message translates to:
  /// **'• Edited'**
  String get edited;

  /// No description provided for @moduleActive.
  ///
  /// In en, this message translates to:
  /// **'Experimental CHIRP module: {name}'**
  String moduleActive(String name);

  /// No description provided for @menuNew.
  ///
  /// In en, this message translates to:
  /// **'New'**
  String get menuNew;

  /// No description provided for @newBlank.
  ///
  /// In en, this message translates to:
  /// **'Blank configuration'**
  String get newBlank;

  /// No description provided for @newGmrs.
  ///
  /// In en, this message translates to:
  /// **'GMRS starter template'**
  String get newGmrs;

  /// No description provided for @newMarine.
  ///
  /// In en, this message translates to:
  /// **'Marine VHF template'**
  String get newMarine;

  /// No description provided for @newRestoreStock.
  ///
  /// In en, this message translates to:
  /// **'Restore stock channels'**
  String get newRestoreStock;

  /// No description provided for @openChannelFile.
  ///
  /// In en, this message translates to:
  /// **'Open channel file'**
  String get openChannelFile;

  /// No description provided for @loadModule.
  ///
  /// In en, this message translates to:
  /// **'Load CHIRP driver module…'**
  String get loadModule;

  /// No description provided for @loadModuleShort.
  ///
  /// In en, this message translates to:
  /// **'Load driver…'**
  String get loadModuleShort;

  /// No description provided for @unloadModule.
  ///
  /// In en, this message translates to:
  /// **'Unload CHIRP module'**
  String get unloadModule;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @saveAs.
  ///
  /// In en, this message translates to:
  /// **'Save as…'**
  String get saveAs;

  /// No description provided for @printChannelList.
  ///
  /// In en, this message translates to:
  /// **'Print channel list…'**
  String get printChannelList;

  /// No description provided for @print.
  ///
  /// In en, this message translates to:
  /// **'Print'**
  String get print;

  /// No description provided for @help.
  ///
  /// In en, this message translates to:
  /// **'Help'**
  String get help;

  /// No description provided for @reportProblem.
  ///
  /// In en, this message translates to:
  /// **'Report a problem…'**
  String get reportProblem;

  /// No description provided for @checkingUpdates.
  ///
  /// In en, this message translates to:
  /// **'Checking for updates...'**
  String get checkingUpdates;

  /// No description provided for @checkUpdates.
  ///
  /// In en, this message translates to:
  /// **'Check for updates'**
  String get checkUpdates;

  /// No description provided for @showSummary.
  ///
  /// In en, this message translates to:
  /// **'Show channel summary'**
  String get showSummary;

  /// No description provided for @hideSummary.
  ///
  /// In en, this message translates to:
  /// **'Hide channel summary to show more channels'**
  String get hideSummary;

  /// No description provided for @metricChannels.
  ///
  /// In en, this message translates to:
  /// **'Channels'**
  String get metricChannels;

  /// No description provided for @metricScan.
  ///
  /// In en, this message translates to:
  /// **'Scan enabled'**
  String get metricScan;

  /// No description provided for @metricAttention.
  ///
  /// In en, this message translates to:
  /// **'Needs attention'**
  String get metricAttention;

  /// No description provided for @editBanksZones.
  ///
  /// In en, this message translates to:
  /// **'Edit banks / zones'**
  String get editBanksZones;

  /// No description provided for @banksZonesTitle.
  ///
  /// In en, this message translates to:
  /// **'Banks and zones'**
  String get banksZonesTitle;

  /// No description provided for @banksZonesHelp.
  ///
  /// In en, this message translates to:
  /// **'Use this editor to rename zones or banks and choose which channel memories belong to each one. Some radios allow a channel in multiple zones. An empty “New zone” entry is created by adding a channel to it. Changes are written with the channels; review them before writing because membership follows the channel memory number.'**
  String get banksZonesHelp;

  /// No description provided for @radioSection.
  ///
  /// In en, this message translates to:
  /// **'Radio section'**
  String get radioSection;

  /// No description provided for @zoneChannelCount.
  ///
  /// In en, this message translates to:
  /// **'{name} ({count} channels)'**
  String zoneChannelCount(String name, int count);

  /// No description provided for @radioSectionsTitle.
  ///
  /// In en, this message translates to:
  /// **'Radio sections'**
  String get radioSectionsTitle;

  /// No description provided for @radioSectionsHelp.
  ///
  /// In en, this message translates to:
  /// **'This radio exposes separate channel sections or subdevices. Choose a section to view and edit its channels. Writing preserves the other sections in the saved radio image. Banks and zones are edited separately.'**
  String get radioSectionsHelp;

  /// No description provided for @search.
  ///
  /// In en, this message translates to:
  /// **'Search'**
  String get search;

  /// No description provided for @searchHint.
  ///
  /// In en, this message translates to:
  /// **'Search name, frequency, or note'**
  String get searchHint;

  /// No description provided for @clearChannelSearch.
  ///
  /// In en, this message translates to:
  /// **'Clear channel search'**
  String get clearChannelSearch;

  /// No description provided for @bulkEditTip.
  ///
  /// In en, this message translates to:
  /// **'Bulk edit {count} selected channels'**
  String bulkEditTip(int count);

  /// No description provided for @clearSelectedTip.
  ///
  /// In en, this message translates to:
  /// **'Clear {count} selected channels'**
  String clearSelectedTip(int count);

  /// No description provided for @duplicateChannel.
  ///
  /// In en, this message translates to:
  /// **'Duplicate channel'**
  String get duplicateChannel;

  /// No description provided for @addChannel.
  ///
  /// In en, this message translates to:
  /// **'Add channel'**
  String get addChannel;

  /// No description provided for @slots.
  ///
  /// In en, this message translates to:
  /// **'Slots'**
  String get slots;

  /// No description provided for @showEmptySlotsTip.
  ///
  /// In en, this message translates to:
  /// **'Show every memory slot, including empty ones'**
  String get showEmptySlotsTip;

  /// No description provided for @clearColumnFilters.
  ///
  /// In en, this message translates to:
  /// **'Clear column filters'**
  String get clearColumnFilters;

  /// No description provided for @editSelected.
  ///
  /// In en, this message translates to:
  /// **'Edit {count} selected'**
  String editSelected(int count);

  /// No description provided for @duplicate.
  ///
  /// In en, this message translates to:
  /// **'Duplicate'**
  String get duplicate;

  /// No description provided for @showEmptySlots.
  ///
  /// In en, this message translates to:
  /// **'Show empty slots'**
  String get showEmptySlots;

  /// No description provided for @clearFilters.
  ///
  /// In en, this message translates to:
  /// **'Clear filters'**
  String get clearFilters;

  /// No description provided for @openShort.
  ///
  /// In en, this message translates to:
  /// **'Open…'**
  String get openShort;

  /// No description provided for @welcomeTitle.
  ///
  /// In en, this message translates to:
  /// **'What would you like to do?'**
  String get welcomeTitle;

  /// No description provided for @welcomeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Open an existing CHIRP file or read channels directly from your radio.'**
  String get welcomeSubtitle;

  /// No description provided for @welcomeLoadTitle.
  ///
  /// In en, this message translates to:
  /// **'Load configuration'**
  String get welcomeLoadTitle;

  /// No description provided for @welcomeLoadBody.
  ///
  /// In en, this message translates to:
  /// **'Open a CHIRP CSV or native image file and continue editing.'**
  String get welcomeLoadBody;

  /// No description provided for @welcomeLoadHelp.
  ///
  /// In en, this message translates to:
  /// **'Open a CHIRP-compatible CSV or native radio image. Native images retain the selected model and stored image needed for radio transfer.'**
  String get welcomeLoadHelp;

  /// No description provided for @welcomeReadTitle.
  ///
  /// In en, this message translates to:
  /// **'Read channels from a radio'**
  String get welcomeReadTitle;

  /// No description provided for @welcomeReadBody.
  ///
  /// In en, this message translates to:
  /// **'Connect a programming cable and import the radio’s current channels.'**
  String get welcomeReadBody;

  /// No description provided for @welcomeConnect.
  ///
  /// In en, this message translates to:
  /// **'Connect radio'**
  String get welcomeConnect;

  /// No description provided for @welcomeReadHelp.
  ///
  /// In en, this message translates to:
  /// **'Open the radio connection screen, choose your cable and exact model, then choose Read channels from the radio. Settings are read separately from the Radio settings page.'**
  String get welcomeReadHelp;

  /// No description provided for @welcomeRepeatersTitle.
  ///
  /// In en, this message translates to:
  /// **'Find nearby repeaters'**
  String get welcomeRepeatersTitle;

  /// No description provided for @welcomeRepeatersBody.
  ///
  /// In en, this message translates to:
  /// **'Search RepeaterBook and add repeater channels.'**
  String get welcomeRepeatersBody;

  /// No description provided for @welcomeRepeatersHelp.
  ///
  /// In en, this message translates to:
  /// **'Search RepeaterBook for amateur and GMRS repeaters, preview matching repeaters, and add selected channels to the current library.'**
  String get welcomeRepeatersHelp;

  /// No description provided for @welcomeTip.
  ///
  /// In en, this message translates to:
  /// **'Writing to a radio requires reading a matching image from it first. You can plan or edit a CSV anytime, but radio writes stay locked until a read completes.'**
  String get welcomeTip;

  /// No description provided for @updateCheckFailed.
  ///
  /// In en, this message translates to:
  /// **'Couldn’t check for updates'**
  String get updateCheckFailed;

  /// No description provided for @updateCheckFailedHint.
  ///
  /// In en, this message translates to:
  /// **'You can also download the latest version from newchirp.net.'**
  String get updateCheckFailedHint;

  /// No description provided for @aboutSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Application information and open-source licenses'**
  String get aboutSubtitle;

  /// No description provided for @freqRefTitle.
  ///
  /// In en, this message translates to:
  /// **'Frequency Reference'**
  String get freqRefTitle;

  /// No description provided for @freqRefUsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'United States Part 95 FRS/GMRS channel plan'**
  String get freqRefUsSubtitle;

  /// No description provided for @settingsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Radio-wide options exposed by the selected driver'**
  String get settingsSubtitle;

  /// No description provided for @aboutTagline.
  ///
  /// In en, this message translates to:
  /// **'Desktop radio programmer · Version {version}'**
  String aboutTagline(String version);

  /// No description provided for @contributor.
  ///
  /// In en, this message translates to:
  /// **'Contributor'**
  String get contributor;

  /// No description provided for @chirpLayerTitle.
  ///
  /// In en, this message translates to:
  /// **'CHIRP compatibility layer'**
  String get chirpLayerTitle;

  /// No description provided for @chirpLayerBody1.
  ///
  /// In en, this message translates to:
  /// **'NewChirp uses the CHIRP driver tree for radio hardware compatibility. CHIRP copyright is held by its contributors, and CHIRP is free software licensed under the GNU General Public License, version 3 or (at your option) any later version.'**
  String get chirpLayerBody1;

  /// No description provided for @chirpLayerBody2.
  ///
  /// In en, this message translates to:
  /// **'NewChirp also develops its own drivers for radios that do not yet have a CHIRP driver or whose existing CHIRP driver does not work correctly. These NewChirp-maintained drivers are released under GPLv3-or-later and are available for incorporation into upstream CHIRP under the same license, subject to CHIRP maintainer review and acceptance.'**
  String get chirpLayerBody2;

  /// No description provided for @chirpSource.
  ///
  /// In en, this message translates to:
  /// **'CHIRP project and source: {url}'**
  String chirpSource(String url);

  /// No description provided for @newchirpSource.
  ///
  /// In en, this message translates to:
  /// **'NewChirp project and source: {url}'**
  String newchirpSource(String url);

  /// No description provided for @licensesTitle.
  ///
  /// In en, this message translates to:
  /// **'Open-source licenses'**
  String get licensesTitle;

  /// No description provided for @licensesBody.
  ///
  /// In en, this message translates to:
  /// **'The complete CHIRP GPL text and pySerial, libusb, and Flutter dependency licenses are included with this application.'**
  String get licensesBody;

  /// No description provided for @viewLicenses.
  ///
  /// In en, this message translates to:
  /// **'View complete licenses'**
  String get viewLicenses;

  /// No description provided for @notAffiliated.
  ///
  /// In en, this message translates to:
  /// **'NewChirp is an independent interface and is not affiliated with or endorsed by the CHIRP project.'**
  String get notAffiliated;

  /// No description provided for @settingsIntro.
  ///
  /// In en, this message translates to:
  /// **'Adjust radio-wide options such as squelch, backlight, VOX, and other controls exposed by the selected CHIRP driver.'**
  String get settingsIntro;

  /// No description provided for @settingsNoModel.
  ///
  /// In en, this message translates to:
  /// **'No radio model selected. Open Radio connection first.'**
  String get settingsNoModel;

  /// No description provided for @settingsNoCable.
  ///
  /// In en, this message translates to:
  /// **'No programming cable selected'**
  String get settingsNoCable;

  /// No description provided for @settingsReadFromRadio.
  ///
  /// In en, this message translates to:
  /// **'read from radio'**
  String get settingsReadFromRadio;

  /// No description provided for @settingsSnapshotAvailable.
  ///
  /// In en, this message translates to:
  /// **'saved snapshot available'**
  String get settingsSnapshotAvailable;

  /// No description provided for @settingsLoading.
  ///
  /// In en, this message translates to:
  /// **'Loading radio settings...'**
  String get settingsLoading;

  /// No description provided for @settingsUnsupportedTitle.
  ///
  /// In en, this message translates to:
  /// **'This radio does not expose global settings'**
  String get settingsUnsupportedTitle;

  /// No description provided for @settingsUnsupportedBody.
  ///
  /// In en, this message translates to:
  /// **'The selected CHIRP driver does not provide radio-wide settings. Per-channel settings are still available in the channel editor.'**
  String get settingsUnsupportedBody;

  /// No description provided for @settingsLoadError.
  ///
  /// In en, this message translates to:
  /// **'Could not load radio settings'**
  String get settingsLoadError;

  /// No description provided for @settingsReadTitle.
  ///
  /// In en, this message translates to:
  /// **'Read radio settings'**
  String get settingsReadTitle;

  /// No description provided for @settingsReadBodyConnected.
  ///
  /// In en, this message translates to:
  /// **'Read the current settings directly from the connected radio. This refreshes the saved snapshot and settings only; the current channel list is not changed.'**
  String get settingsReadBodyConnected;

  /// No description provided for @settingsReadBodyDisconnected.
  ///
  /// In en, this message translates to:
  /// **'Select the programming cable and exact model on Radio connection, then read the radio to load its settings.'**
  String get settingsReadBodyDisconnected;

  /// No description provided for @openRadioConnection.
  ///
  /// In en, this message translates to:
  /// **'Open radio connection'**
  String get openRadioConnection;

  /// No description provided for @settingsNotLoadedTitle.
  ///
  /// In en, this message translates to:
  /// **'Settings have not loaded yet'**
  String get settingsNotLoadedTitle;

  /// No description provided for @settingsNotLoadedConnected.
  ///
  /// In en, this message translates to:
  /// **'Read the current values from the connected radio, or use the saved radio snapshot for cached values.'**
  String get settingsNotLoadedConnected;

  /// No description provided for @settingsNotLoadedSnapshot.
  ///
  /// In en, this message translates to:
  /// **'Use the saved radio snapshot to load cached values.'**
  String get settingsNotLoadedSnapshot;

  /// No description provided for @readSettingsFromRadio.
  ///
  /// In en, this message translates to:
  /// **'Read current settings from radio'**
  String get readSettingsFromRadio;

  /// No description provided for @useSavedSnapshot.
  ///
  /// In en, this message translates to:
  /// **'Use saved radio snapshot'**
  String get useSavedSnapshot;

  /// No description provided for @uiDefaultsComeFromChannelOnlyFields.
  ///
  /// In en, this message translates to:
  /// **'Defaults come from channel {p0}. Only fields you change here are applied to all selected channels.'**
  String uiDefaultsComeFromChannelOnlyFields(Object p0);

  /// No description provided for @uiSelectedChannelsNeedChanges.
  ///
  /// In en, this message translates to:
  /// **'Selected channels need changes'**
  String get uiSelectedChannelsNeedChanges;

  /// No description provided for @uiBackToEditor.
  ///
  /// In en, this message translates to:
  /// **'Back to editor'**
  String get uiBackToEditor;

  /// No description provided for @uiUpdatedSelectedChannels.
  ///
  /// In en, this message translates to:
  /// **'Updated {p0} selected channels'**
  String uiUpdatedSelectedChannels(Object p0);

  /// No description provided for @uiConnectTheAndChooseItsPort.
  ///
  /// In en, this message translates to:
  /// **'Connect the {p0} and choose its port to read {p1}.'**
  String uiConnectTheAndChooseItsPort(Object p0, Object p1);

  /// No description provided for @uiBankAndZoneChangesAreReady.
  ///
  /// In en, this message translates to:
  /// **'Bank and zone changes are ready. Write them with the channels.'**
  String get uiBankAndZoneChangesAreReady;

  /// No description provided for @uiCouldnTCompleteThatAction.
  ///
  /// In en, this message translates to:
  /// **'Couldn’t complete that action'**
  String get uiCouldnTCompleteThatAction;

  /// No description provided for @uiMoreInfo.
  ///
  /// In en, this message translates to:
  /// **'More Info:'**
  String get uiMoreInfo;

  /// No description provided for @uiSubmitBugReport.
  ///
  /// In en, this message translates to:
  /// **'Submit Bug Report'**
  String get uiSubmitBugReport;

  /// No description provided for @uiLoadExperimentalChirpModule.
  ///
  /// In en, this message translates to:
  /// **'Load experimental CHIRP module?'**
  String get uiLoadExperimentalChirpModule;

  /// No description provided for @uiChirpModulesAreExecutablePythonCode.
  ///
  /// In en, this message translates to:
  /// **'CHIRP modules are executable Python code. NewChirp runs the module in a sandbox that blocks your home folder, other drives, and the network. The module can still use the selected radio and the files for this session.'**
  String get uiChirpModulesAreExecutablePythonCode;

  /// No description provided for @uiOnlyLoadAModuleFromA.
  ///
  /// In en, this message translates to:
  /// **'Only load a module from a source you trust. A bad module can still damage the radio. The module remains active only for this NewChirp session. Select the radio model and read the radio again before writing.'**
  String get uiOnlyLoadAModuleFromA;

  /// No description provided for @uiLoadModule.
  ///
  /// In en, this message translates to:
  /// **'Load module'**
  String get uiLoadModule;

  /// No description provided for @uiMovedToChannel.
  ///
  /// In en, this message translates to:
  /// **'Moved {p0} to channel {p1}'**
  String uiMovedToChannel(Object p0, Object p1);

  /// No description provided for @uiThisRadioHasFixedChannelLocations.
  ///
  /// In en, this message translates to:
  /// **'This radio has fixed channel locations, so empty slots cannot be inserted.'**
  String get uiThisRadioHasFixedChannelLocations;

  /// No description provided for @uiInsertedAnEmptySlotBeforeChannel.
  ///
  /// In en, this message translates to:
  /// **'Inserted an empty slot before channel {p0}'**
  String uiInsertedAnEmptySlotBeforeChannel(Object p0);

  /// No description provided for @uiThisRadioHasFixedChannelLocations2.
  ///
  /// In en, this message translates to:
  /// **'This radio has fixed channel locations, so empty slots cannot be removed.'**
  String get uiThisRadioHasFixedChannelLocations2;

  /// No description provided for @uiRemovedEmptySlot.
  ///
  /// In en, this message translates to:
  /// **'Removed empty slot {p0}'**
  String uiRemovedEmptySlot(Object p0);

  /// No description provided for @uiRepeaterbookResults.
  ///
  /// In en, this message translates to:
  /// **'RepeaterBook results'**
  String get uiRepeaterbookResults;

  /// No description provided for @uiMacosBlockedTheSaveLocation.
  ///
  /// In en, this message translates to:
  /// **'macOS blocked the save location'**
  String get uiMacosBlockedTheSaveLocation;

  /// No description provided for @uiNewchirpDoesNotHavePermissionTo.
  ///
  /// In en, this message translates to:
  /// **'NewChirp does not have permission to write to this folder. Choose another folder now, or allow NewChirp access in System Settings > Privacy & Security > Files and Folders.'**
  String get uiNewchirpDoesNotHavePermissionTo;

  /// No description provided for @uiChooseAnotherFolder.
  ///
  /// In en, this message translates to:
  /// **'Choose another folder'**
  String get uiChooseAnotherFolder;

  /// No description provided for @uiStart.
  ///
  /// In en, this message translates to:
  /// **'Start {p0}?'**
  String uiStart(Object p0);

  /// No description provided for @uiKeepCurrentList.
  ///
  /// In en, this message translates to:
  /// **'Keep current list'**
  String get uiKeepCurrentList;

  /// No description provided for @uiDiscardAndContinue.
  ///
  /// In en, this message translates to:
  /// **'Discard and continue'**
  String get uiDiscardAndContinue;

  /// No description provided for @uiMarineVhfTemplate.
  ///
  /// In en, this message translates to:
  /// **'{p0} Marine VHF template'**
  String uiMarineVhfTemplate(Object p0);

  /// No description provided for @uiStockChannels.
  ///
  /// In en, this message translates to:
  /// **'stock channels'**
  String get uiStockChannels;

  /// No description provided for @uiDiscardUnsavedSettingsChanges.
  ///
  /// In en, this message translates to:
  /// **'Discard unsaved settings changes?'**
  String get uiDiscardUnsavedSettingsChanges;

  /// No description provided for @uiUsingTheSavedRadioSnapshotWill.
  ///
  /// In en, this message translates to:
  /// **'Using the saved radio snapshot will replace the unsaved settings changes shown on this page.'**
  String get uiUsingTheSavedRadioSnapshotWill;

  /// No description provided for @uiUseSavedSnapshot.
  ///
  /// In en, this message translates to:
  /// **'Use saved snapshot'**
  String get uiUseSavedSnapshot;

  /// No description provided for @uiReplaceUnsavedSettingsChanges.
  ///
  /// In en, this message translates to:
  /// **'Replace unsaved settings changes?'**
  String get uiReplaceUnsavedSettingsChanges;

  /// No description provided for @uiReadingSettingsFromTheRadioWill.
  ///
  /// In en, this message translates to:
  /// **'Reading settings from the radio will replace the unsaved settings changes shown on this page. The current channel list is not changed.'**
  String get uiReadingSettingsFromTheRadioWill;

  /// No description provided for @uiReadSettings.
  ///
  /// In en, this message translates to:
  /// **'Read settings'**
  String get uiReadSettings;

  /// No description provided for @uiWhereShouldTheNewChannelGo.
  ///
  /// In en, this message translates to:
  /// **'Where should the new channel go?'**
  String get uiWhereShouldTheNewChannelGo;

  /// No description provided for @uiAtTheEnd.
  ///
  /// In en, this message translates to:
  /// **'At the end'**
  String get uiAtTheEnd;

  /// No description provided for @uiBeforeTheSelectedChannel.
  ///
  /// In en, this message translates to:
  /// **'Before the selected channel'**
  String get uiBeforeTheSelectedChannel;

  /// No description provided for @uiAfterTheSelectedChannel.
  ///
  /// In en, this message translates to:
  /// **'After the selected channel'**
  String get uiAfterTheSelectedChannel;

  /// No description provided for @uiChannelAdded.
  ///
  /// In en, this message translates to:
  /// **'Channel {p0} added'**
  String uiChannelAdded(Object p0);

  /// No description provided for @uiThisRadioHasFixedChannelLocations3.
  ///
  /// In en, this message translates to:
  /// **'This radio has fixed channel locations. New channels can only be added after the final channel.'**
  String get uiThisRadioHasFixedChannelLocations3;

  /// No description provided for @uiOverwriteChannels.
  ///
  /// In en, this message translates to:
  /// **'Overwrite {p0} channels?'**
  String uiOverwriteChannels(Object p0);

  /// No description provided for @uiTheDestinationRangeThroughContainsChannels.
  ///
  /// In en, this message translates to:
  /// **'The destination range {p0} through {p1} contains {p2} channels with data. Pasting will replace them.'**
  String uiTheDestinationRangeThroughContainsChannels(
    Object p0,
    Object p1,
    Object p2,
  );

  /// No description provided for @uiOverwriteChannels2.
  ///
  /// In en, this message translates to:
  /// **'Overwrite channels'**
  String get uiOverwriteChannels2;

  /// No description provided for @uiOverwriteChannel.
  ///
  /// In en, this message translates to:
  /// **'Overwrite channel {p0}?'**
  String uiOverwriteChannel(Object p0);

  /// No description provided for @uiOverwriteChannel2.
  ///
  /// In en, this message translates to:
  /// **'Overwrite channel'**
  String get uiOverwriteChannel2;

  /// No description provided for @uiClearedChannelsUseCmdCtrlZ.
  ///
  /// In en, this message translates to:
  /// **'Cleared {p0} channels. Use Cmd/Ctrl+Z to undo.'**
  String uiClearedChannelsUseCmdCtrlZ(Object p0);

  /// No description provided for @uiStaysInTheRadioTheName.
  ///
  /// In en, this message translates to:
  /// **'{p0} stays in the radio. The name is cleared and the plain repeater frequency is back.'**
  String uiStaysInTheRadioTheName(Object p0);

  /// No description provided for @uiAndMoreChannels.
  ///
  /// In en, this message translates to:
  /// **'…and {p0} more channels.'**
  String uiAndMoreChannels(Object p0);

  /// No description provided for @uiNamesAreConvertedOnlyWhenThe.
  ///
  /// In en, this message translates to:
  /// **'Names are converted only when the selected radio requires it. Custom frequencies may require a channel outside the radio\'s locked memory range.'**
  String get uiNamesAreConvertedOnlyWhenThe;

  /// No description provided for @uiStopWritingTheRadio.
  ///
  /// In en, this message translates to:
  /// **'Stop writing the radio?'**
  String get uiStopWritingTheRadio;

  /// No description provided for @uiTheRadioIsBeingWrittenNow.
  ///
  /// In en, this message translates to:
  /// **'The radio is being written now. Some radios take a minute or two, and the elapsed time shows the write is still running. Stopping partway can leave part of the radio\'s memory half-written; it may then need a power cycle and a fresh write.'**
  String get uiTheRadioIsBeingWrittenNow;

  /// No description provided for @uiStopAnyway.
  ///
  /// In en, this message translates to:
  /// **'Stop anyway'**
  String get uiStopAnyway;

  /// No description provided for @uiKeepWriting.
  ///
  /// In en, this message translates to:
  /// **'Keep writing'**
  String get uiKeepWriting;

  /// No description provided for @uiLater.
  ///
  /// In en, this message translates to:
  /// **'Later'**
  String get uiLater;

  /// No description provided for @uiOpenDownloadPage.
  ///
  /// In en, this message translates to:
  /// **'Open download page'**
  String get uiOpenDownloadPage;

  /// No description provided for @uiDownloadAndInstall.
  ///
  /// In en, this message translates to:
  /// **'Download and install'**
  String get uiDownloadAndInstall;

  /// No description provided for @uiFinishTheCurrentOperationFirst.
  ///
  /// In en, this message translates to:
  /// **'Finish the current operation first'**
  String get uiFinishTheCurrentOperationFirst;

  /// No description provided for @uiWaitForTheCurrentRadioOr.
  ///
  /// In en, this message translates to:
  /// **'Wait for the current radio or file operation to finish before installing NewChirp.'**
  String get uiWaitForTheCurrentRadioOr;

  /// No description provided for @uiSaveRadioSettingsFirst.
  ///
  /// In en, this message translates to:
  /// **'Save radio settings first'**
  String get uiSaveRadioSettingsFirst;

  /// No description provided for @uiYouHaveRadioSettingChangesThat.
  ///
  /// In en, this message translates to:
  /// **'You have radio setting changes that have not been written. Save those settings before installing the update.'**
  String get uiYouHaveRadioSettingChangesThat;

  /// No description provided for @uiSaveYourChannelChangesFirst.
  ///
  /// In en, this message translates to:
  /// **'Save your channel changes first'**
  String get uiSaveYourChannelChangesFirst;

  /// No description provided for @uiNewchirpWillCloseToInstallThe.
  ///
  /// In en, this message translates to:
  /// **'NewChirp will close to install the update. Save the current channel list before continuing.'**
  String get uiNewchirpWillCloseToInstallThe;

  /// No description provided for @uiSaveAndContinue.
  ///
  /// In en, this message translates to:
  /// **'Save and continue'**
  String get uiSaveAndContinue;

  /// No description provided for @uiInstallingNewchirpUpdate.
  ///
  /// In en, this message translates to:
  /// **'Installing NewChirp update'**
  String get uiInstallingNewchirpUpdate;

  /// No description provided for @uiNewchirpWillCloseAndReopenAutomatically.
  ///
  /// In en, this message translates to:
  /// **'NewChirp will close and reopen automatically when the installer is ready.'**
  String get uiNewchirpWillCloseAndReopenAutomatically;

  /// No description provided for @uiUpdateCouldNotBeInstalled.
  ///
  /// In en, this message translates to:
  /// **'Update could not be installed'**
  String get uiUpdateCouldNotBeInstalled;

  /// No description provided for @uiYouCanStillDownloadTheLatest.
  ///
  /// In en, this message translates to:
  /// **'{p0}\n\nYou can still download the latest version from newchirp.net.'**
  String uiYouCanStillDownloadTheLatest(Object p0);

  /// No description provided for @uiCouldnTOpenYourBrowser.
  ///
  /// In en, this message translates to:
  /// **'Couldn’t open your browser'**
  String get uiCouldnTOpenYourBrowser;

  /// No description provided for @uiNewchirpCouldNotStartTheBrowser.
  ///
  /// In en, this message translates to:
  /// **'NewChirp could not start the browser on this computer. Open this address yourself to get the update:\n\n{p0}'**
  String uiNewchirpCouldNotStartTheBrowser(Object p0);

  /// No description provided for @uiCopyLink.
  ///
  /// In en, this message translates to:
  /// **'Copy link'**
  String get uiCopyLink;

  /// No description provided for @uiYouReUpToDate.
  ///
  /// In en, this message translates to:
  /// **'You’re up to date'**
  String get uiYouReUpToDate;

  /// No description provided for @uiNewchirpIsTheLatestVersion.
  ///
  /// In en, this message translates to:
  /// **'NewChirp {p0} is the latest version.'**
  String uiNewchirpIsTheLatestVersion(Object p0);

  /// No description provided for @uiChannelIsOccupied.
  ///
  /// In en, this message translates to:
  /// **'Channel {p0} is occupied'**
  String uiChannelIsOccupied(Object p0);

  /// No description provided for @uiReplace.
  ///
  /// In en, this message translates to:
  /// **'Replace'**
  String get uiReplace;

  /// No description provided for @uiSwap.
  ///
  /// In en, this message translates to:
  /// **'Swap'**
  String get uiSwap;

  /// No description provided for @uiMoveAndShift.
  ///
  /// In en, this message translates to:
  /// **'Move and shift'**
  String get uiMoveAndShift;

  /// No description provided for @uiChannelsScanEnabledNeedAttention.
  ///
  /// In en, this message translates to:
  /// **'{p0} channels · {p1} scan enabled · {p2} need attention'**
  String uiChannelsScanEnabledNeedAttention(Object p0, Object p1, Object p2);

  /// No description provided for @uiReview.
  ///
  /// In en, this message translates to:
  /// **'Review'**
  String get uiReview;

  /// No description provided for @uiNoRadioImageLoadedEditingAnd.
  ///
  /// In en, this message translates to:
  /// **'No radio image loaded. Editing and CSV export work, but writing stays locked until you read from this radio.'**
  String get uiNoRadioImageLoadedEditingAnd;

  /// No description provided for @uiChannelEditing.
  ///
  /// In en, this message translates to:
  /// **'Channel editing'**
  String get uiChannelEditing;

  /// No description provided for @uiAddLetsYouPlaceANew.
  ///
  /// In en, this message translates to:
  /// **'Add lets you place a new channel at the end, before the selected channel, or after it. Before and after shift following channels through the radio memory slots. Duplicate copies the selected row, and Delete removes it after confirmation. Double-click any row to edit all of its fields. Right-click a row to copy, cut, paste, duplicate, or clear it. Copying or cutting a multi-row selection copies the active channels as a block; paste places the block at the target row. Click selects one row. Shift-click selects a range, and Cmd/Ctrl-click toggles individual rows. Use Bulk edit to change channel properties on all selected rows; only fields you modify are applied. Right-click and choose Properties for the same editor. Drag the handle at the left edge of a row to move it; intervening channels shift through the same memory slots. Show empty slots keeps the radio memory layout visible; double-click an empty slot to create a channel there. Clear removes the selected row or all selected rows from the radio on the next write. Use Cmd/Ctrl+Z to undo and Cmd/Ctrl+Shift+Z to redo.'**
  String get uiAddLetsYouPlaceANew;

  /// No description provided for @uiChooseAPrinter.
  ///
  /// In en, this message translates to:
  /// **'Choose a printer'**
  String get uiChooseAPrinter;

  /// No description provided for @uiPrintJobSent.
  ///
  /// In en, this message translates to:
  /// **'Print job sent'**
  String get uiPrintJobSent;

  /// No description provided for @uiWasSentTo.
  ///
  /// In en, this message translates to:
  /// **'{p0} was sent to {p1}.'**
  String uiWasSentTo(Object p0, Object p1);

  /// No description provided for @uiUsFrsGmrs.
  ///
  /// In en, this message translates to:
  /// **'US FRS / GMRS'**
  String get uiUsFrsGmrs;

  /// No description provided for @uiReferenceSourceVerifyCurrentNationalRules.
  ///
  /// In en, this message translates to:
  /// **'Reference source: {p0} Verify current national rules before transmitting.'**
  String uiReferenceSourceVerifyCurrentNationalRules(Object p0);

  /// No description provided for @uiGmrsFrsFrequencyReference.
  ///
  /// In en, this message translates to:
  /// **'GMRS & FRS Frequency Reference'**
  String get uiGmrsFrsFrequencyReference;

  /// No description provided for @uiUnitedStatesPartChannelPlanColor.
  ///
  /// In en, this message translates to:
  /// **'United States Part 95 channel plan - color-coded by frequency band and power class.'**
  String get uiUnitedStatesPartChannelPlanColor;

  /// No description provided for @uiRepeaterPairsGmrsOnly.
  ///
  /// In en, this message translates to:
  /// **'Repeater Pairs (GMRS Only)'**
  String get uiRepeaterPairsGmrsOnly;

  /// No description provided for @uiKeyNotes.
  ///
  /// In en, this message translates to:
  /// **'Key notes'**
  String get uiKeyNotes;

  /// No description provided for @uiAllFrequenciesAreInMhzGmrs.
  ///
  /// In en, this message translates to:
  /// **'All frequencies are in MHz. GMRS requires an FCC license; FRS is license-by-rule.\nGMRS mobile/base radios may not transmit on channels 8-14. Repeater inputs are GMRS-only.\nCommunity convention: Channel 20 (462.675 MHz) with CTCSS 141.3 Hz is often used as a travel/assistance channel.\nReference only - verify against current FCC Part 95 rules and your radio manual.'**
  String get uiAllFrequenciesAreInMhzGmrs;

  /// No description provided for @uiNoEditableOptionsInThisGroup.
  ///
  /// In en, this message translates to:
  /// **'No editable options in this group.'**
  String get uiNoEditableOptionsInThisGroup;

  /// No description provided for @uiKeepTheRadioPoweredOnAnd.
  ///
  /// In en, this message translates to:
  /// **'Keep the radio powered on and the cable connected.'**
  String get uiKeepTheRadioPoweredOnAnd;

  /// No description provided for @uiThisSettingTypeIsNotSupported.
  ///
  /// In en, this message translates to:
  /// **'{p0}: this setting type is not supported yet.'**
  String uiThisSettingTypeIsNotSupported(Object p0);

  /// No description provided for @uiSearchAbbreviationsOrDefinitions.
  ///
  /// In en, this message translates to:
  /// **'Search abbreviations or definitions'**
  String get uiSearchAbbreviationsOrDefinitions;

  /// No description provided for @uiNoMatchingTerms.
  ///
  /// In en, this message translates to:
  /// **'No matching terms.'**
  String get uiNoMatchingTerms;

  /// No description provided for @uiThanksTheDiagnosticLogAndError.
  ///
  /// In en, this message translates to:
  /// **'Thanks. The diagnostic log and error details were sent to the NewChirp developer.'**
  String get uiThanksTheDiagnosticLogAndError;

  /// No description provided for @uiYourEmail.
  ///
  /// In en, this message translates to:
  /// **'Your email'**
  String get uiYourEmail;

  /// No description provided for @uiUsedOnlyIfTheDeveloperNeeds.
  ///
  /// In en, this message translates to:
  /// **'Used only if the developer needs more information.'**
  String get uiUsedOnlyIfTheDeveloperNeeds;

  /// No description provided for @uiWhatWereYouTryingToDo.
  ///
  /// In en, this message translates to:
  /// **'What were you trying to do?'**
  String get uiWhatWereYouTryingToDo;

  /// No description provided for @uiTheReportIncludesAppAndOperating.
  ///
  /// In en, this message translates to:
  /// **'The report includes app and operating-system versions, the selected radio and serial port, and recent diagnostic events. Channel contents and loaded files are not logged.'**
  String get uiTheReportIncludesAppAndOperating;

  /// No description provided for @uiPreviewDiagnosticEvents.
  ///
  /// In en, this message translates to:
  /// **'Preview {p0} diagnostic events'**
  String uiPreviewDiagnosticEvents(Object p0);

  /// No description provided for @uiFilterCounties.
  ///
  /// In en, this message translates to:
  /// **'Filter {p0} counties'**
  String uiFilterCounties(Object p0);

  /// No description provided for @uiFindACounty.
  ///
  /// In en, this message translates to:
  /// **'Find a county'**
  String get uiFindACounty;

  /// No description provided for @uiOfCounties.
  ///
  /// In en, this message translates to:
  /// **'{p0} of {p1} counties'**
  String uiOfCounties(Object p0, Object p1);

  /// No description provided for @uiClearAll.
  ///
  /// In en, this message translates to:
  /// **'Clear all'**
  String get uiClearAll;

  /// No description provided for @uiNoMatchingCounties.
  ///
  /// In en, this message translates to:
  /// **'No matching counties.'**
  String get uiNoMatchingCounties;

  /// No description provided for @uiNoCoordinatesAreAvailableForThese.
  ///
  /// In en, this message translates to:
  /// **'No coordinates are available for these results.'**
  String get uiNoCoordinatesAreAvailableForThese;

  /// No description provided for @uiMappedTapAPinToSelect.
  ///
  /// In en, this message translates to:
  /// **'{p0} mapped • tap a pin to select'**
  String uiMappedTapAPinToSelect(Object p0);

  /// No description provided for @uiSearchARepeaterDirectoryAndAdd.
  ///
  /// In en, this message translates to:
  /// **'Search a repeater directory and add selected channels to your current library. Verify repeater status and access before transmitting.'**
  String get uiSearchARepeaterDirectoryAndAdd;

  /// No description provided for @uiDirectory.
  ///
  /// In en, this message translates to:
  /// **'Directory'**
  String get uiDirectory;

  /// No description provided for @uiMygmrsRequiresAnActiveGmrsLicense.
  ///
  /// In en, this message translates to:
  /// **'myGMRS requires an active GMRS license for repeater frequencies. PL tones and rules require a Premium membership. This sign-in lasts until NewChirp closes.'**
  String get uiMygmrsRequiresAnActiveGmrsLicense;

  /// No description provided for @uiCountry.
  ///
  /// In en, this message translates to:
  /// **'Country'**
  String get uiCountry;

  /// No description provided for @uiSortResults.
  ///
  /// In en, this message translates to:
  /// **'Sort results'**
  String get uiSortResults;

  /// No description provided for @uiSourceOrder.
  ///
  /// In en, this message translates to:
  /// **'Source order'**
  String get uiSourceOrder;

  /// No description provided for @uiFrequency.
  ///
  /// In en, this message translates to:
  /// **'Frequency'**
  String get uiFrequency;

  /// No description provided for @uiCallsignName.
  ///
  /// In en, this message translates to:
  /// **'Callsign / name'**
  String get uiCallsignName;

  /// No description provided for @uiCity.
  ///
  /// In en, this message translates to:
  /// **'City'**
  String get uiCity;

  /// No description provided for @uiCounty.
  ///
  /// In en, this message translates to:
  /// **'County'**
  String get uiCounty;

  /// No description provided for @uiService.
  ///
  /// In en, this message translates to:
  /// **'Service'**
  String get uiService;

  /// No description provided for @uiAmateurGmrs.
  ///
  /// In en, this message translates to:
  /// **'Amateur + GMRS'**
  String get uiAmateurGmrs;

  /// No description provided for @uiAmateurHam.
  ///
  /// In en, this message translates to:
  /// **'Amateur (ham)'**
  String get uiAmateurHam;

  /// No description provided for @uiClearRepeaterSearch.
  ///
  /// In en, this message translates to:
  /// **'Clear repeater search'**
  String get uiClearRepeaterSearch;

  /// No description provided for @uiLatitudeOptional.
  ///
  /// In en, this message translates to:
  /// **'Latitude (optional)'**
  String get uiLatitudeOptional;

  /// No description provided for @uiLongitudeOptional.
  ///
  /// In en, this message translates to:
  /// **'Longitude (optional)'**
  String get uiLongitudeOptional;

  /// No description provided for @uiRadiusKm.
  ///
  /// In en, this message translates to:
  /// **'Radius km'**
  String get uiRadiusKm;

  /// No description provided for @uiOpenRepeatersOnly.
  ///
  /// In en, this message translates to:
  /// **'Open repeaters only'**
  String get uiOpenRepeatersOnly;

  /// No description provided for @uiFmCapableOnly.
  ///
  /// In en, this message translates to:
  /// **'FM-capable only'**
  String get uiFmCapableOnly;

  /// No description provided for @uiSearchAmateurRepeatersInstead.
  ///
  /// In en, this message translates to:
  /// **'Search Amateur repeaters instead'**
  String get uiSearchAmateurRepeatersInstead;

  /// No description provided for @uiFilterLoadedResults.
  ///
  /// In en, this message translates to:
  /// **'Filter loaded results'**
  String get uiFilterLoadedResults;

  /// No description provided for @uiCityCountyCallsignModeServiceOr.
  ///
  /// In en, this message translates to:
  /// **'City, county, callsign, mode, service, or frequency'**
  String get uiCityCountyCallsignModeServiceOr;

  /// No description provided for @uiClearResultFilter.
  ///
  /// In en, this message translates to:
  /// **'Clear result filter'**
  String get uiClearResultFilter;

  /// No description provided for @uiList.
  ///
  /// In en, this message translates to:
  /// **'List'**
  String get uiList;

  /// No description provided for @uiMap.
  ///
  /// In en, this message translates to:
  /// **'Map'**
  String get uiMap;

  /// No description provided for @uiSelectAll.
  ///
  /// In en, this message translates to:
  /// **'Select all'**
  String get uiSelectAll;

  /// No description provided for @uiClear.
  ///
  /// In en, this message translates to:
  /// **'Clear'**
  String get uiClear;

  /// No description provided for @uiDataCourtesyOfRepeaterbookCom.
  ///
  /// In en, this message translates to:
  /// **'Data courtesy of RepeaterBook.com.'**
  String get uiDataCourtesyOfRepeaterbookCom;

  /// No description provided for @uiDragToResize.
  ///
  /// In en, this message translates to:
  /// **'Drag to resize'**
  String get uiDragToResize;

  /// No description provided for @uiInsertEmptySlotBefore.
  ///
  /// In en, this message translates to:
  /// **'Insert empty slot before'**
  String get uiInsertEmptySlotBefore;

  /// No description provided for @uiRemoveEmptySlot.
  ///
  /// In en, this message translates to:
  /// **'Remove empty slot'**
  String get uiRemoveEmptySlot;

  /// No description provided for @uiMove.
  ///
  /// In en, this message translates to:
  /// **'Move {p0}'**
  String uiMove(Object p0);

  /// No description provided for @uiDragRowsToRearrangeChannels.
  ///
  /// In en, this message translates to:
  /// **'Drag rows to rearrange channels'**
  String get uiDragRowsToRearrangeChannels;

  /// No description provided for @uiFilter.
  ///
  /// In en, this message translates to:
  /// **'Filter'**
  String get uiFilter;

  /// No description provided for @uiNoMatchingChannels.
  ///
  /// In en, this message translates to:
  /// **'No matching channels'**
  String get uiNoMatchingChannels;

  /// No description provided for @uiWriteChannelsToRadio.
  ///
  /// In en, this message translates to:
  /// **'Write channels to radio'**
  String get uiWriteChannelsToRadio;

  /// No description provided for @uiThanksTheDiagnosticLogAndProblem.
  ///
  /// In en, this message translates to:
  /// **'Thanks. The diagnostic log and problem details were sent to the NewChirp developer.'**
  String get uiThanksTheDiagnosticLogAndProblem;

  /// No description provided for @uiTheReportIncludesAppAndOperating2.
  ///
  /// In en, this message translates to:
  /// **'The report includes app and operating-system versions, the selected radio, firmware when available, serial port, and recent diagnostic events. Channel contents and loaded files are not logged.'**
  String get uiTheReportIncludesAppAndOperating2;

  /// No description provided for @uiSaveFile.
  ///
  /// In en, this message translates to:
  /// **'Save file'**
  String get uiSaveFile;

  /// No description provided for @uiDoNotShowMeThisMessage.
  ///
  /// In en, this message translates to:
  /// **'Do not show me this message again'**
  String get uiDoNotShowMeThisMessage;

  /// No description provided for @uiMarineVhfChannelTemplate.
  ///
  /// In en, this message translates to:
  /// **'Marine VHF channel template'**
  String get uiMarineVhfChannelTemplate;

  /// No description provided for @uiPlan.
  ///
  /// In en, this message translates to:
  /// **'Plan'**
  String get uiPlan;

  /// No description provided for @uiSource.
  ///
  /// In en, this message translates to:
  /// **'Source: {p0}'**
  String uiSource(Object p0);

  /// No description provided for @uiTheChannelPlanIsSelectedBy.
  ///
  /// In en, this message translates to:
  /// **'The channel plan is selected by regulatory region, not ZIP code. Marine channel assignments are national or international and do not change by postal code.'**
  String get uiTheChannelPlanIsSelectedBy;

  /// No description provided for @uiProgramShipTransmitFrequencies.
  ///
  /// In en, this message translates to:
  /// **'Program ship transmit frequencies'**
  String get uiProgramShipTransmitFrequencies;

  /// No description provided for @uiReceiveOnlyIsTheSafeDefault.
  ///
  /// In en, this message translates to:
  /// **'Receive-only is the safe default. Enable this only when the radio and installation are authorized for marine VHF transmission.'**
  String get uiReceiveOnlyIsTheSafeDefault;

  /// No description provided for @uiMostAmateurTransceiversAreNotType.
  ///
  /// In en, this message translates to:
  /// **'Most amateur transceivers are not type-accepted for marine-band transmit. Prohibited and receive-only channels remain transmission-disabled.'**
  String get uiMostAmateurTransceiversAreNotType;

  /// No description provided for @uiChannelsTransmitCapableReceiveOnly.
  ///
  /// In en, this message translates to:
  /// **'{p0} channels: {p1} transmit-capable, {p2} receive-only.'**
  String uiChannelsTransmitCapableReceiveOnly(Object p0, Object p1, Object p2);

  /// No description provided for @uiAllRowsWillBeAddedReceive.
  ///
  /// In en, this message translates to:
  /// **'All rows will be added receive-only (Duplex \"off\"). The radio will beep and not transmit on them. Check the box above to program transmit frequencies.'**
  String get uiAllRowsWillBeAddedReceive;

  /// No description provided for @uiContinue.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get uiContinue;

  /// No description provided for @uiType.
  ///
  /// In en, this message translates to:
  /// **'Type'**
  String get uiType;

  /// No description provided for @uiThisRadioDoesNotExposeEditable.
  ///
  /// In en, this message translates to:
  /// **'This radio does not expose editable banks.'**
  String get uiThisRadioDoesNotExposeEditable;

  /// No description provided for @uiTheseBanksAreFixedByThe.
  ///
  /// In en, this message translates to:
  /// **'These banks are fixed by the radio and are shown for reference.'**
  String get uiTheseBanksAreFixedByThe;

  /// No description provided for @uiUseTheseChanges.
  ///
  /// In en, this message translates to:
  /// **'Use these changes'**
  String get uiUseTheseChanges;

  /// No description provided for @uiFindAChannel.
  ///
  /// In en, this message translates to:
  /// **'Find a channel'**
  String get uiFindAChannel;

  /// No description provided for @uiChannel.
  ///
  /// In en, this message translates to:
  /// **'Channel {p0}'**
  String uiChannel(Object p0);

  /// No description provided for @uiLoadingRadioCatalog.
  ///
  /// In en, this message translates to:
  /// **'Loading radio catalog…'**
  String get uiLoadingRadioCatalog;

  /// No description provided for @uiActionFailed.
  ///
  /// In en, this message translates to:
  /// **'Action failed'**
  String get uiActionFailed;

  /// No description provided for @uiMacosBlockedNewchirpFromWritingTo.
  ///
  /// In en, this message translates to:
  /// **'{p0}\n\nmacOS blocked NewChirp from writing to that folder. Choose a different save location, or allow NewChirp access under:\n\nSystem Settings > Privacy & Security > Files and Folders > NewChirp\n\nGrant access to Documents, then retry Save.'**
  String uiMacosBlockedNewchirpFromWritingTo(Object p0);

  /// No description provided for @uiOnLinuxThisUsuallyMeansYour.
  ///
  /// In en, this message translates to:
  /// **'{p0}\n\nOn Linux, this usually means your user does not have permission to open the radio programming cable.\n\nFix it with:\n    sudo usermod -aG dialout \$USER\n\nThen log out and back in, reconnect the cable, and try again.\n\nFor the current terminal session only:\n    newgrp dialout'**
  String uiOnLinuxThisUsuallyMeansYour(Object p0);

  /// No description provided for @uiMototrboCpsChannels.
  ///
  /// In en, this message translates to:
  /// **'MOTOTRBO CPS 2.0 channels'**
  String get uiMototrboCpsChannels;

  /// No description provided for @uiCsvChannels.
  ///
  /// In en, this message translates to:
  /// **'CSV channels'**
  String get uiCsvChannels;

  /// No description provided for @uiRefreshingRadioCatalog.
  ///
  /// In en, this message translates to:
  /// **'Refreshing radio catalog…'**
  String get uiRefreshingRadioCatalog;

  /// No description provided for @uiThisChirpImage.
  ///
  /// In en, this message translates to:
  /// **'this CHIRP image'**
  String get uiThisChirpImage;

  /// No description provided for @uiNoEmptyChannelSlotIsAvailable.
  ///
  /// In en, this message translates to:
  /// **'No empty channel slot is available.'**
  String get uiNoEmptyChannelSlotIsAvailable;

  /// No description provided for @uiNoEmptyChannelSlotsAreAvailable.
  ///
  /// In en, this message translates to:
  /// **'No empty channel slots are available for this radio.'**
  String get uiNoEmptyChannelSlotsAreAvailable;

  /// No description provided for @uiSavingChannelLibrary.
  ///
  /// In en, this message translates to:
  /// **'Saving channel library…'**
  String get uiSavingChannelLibrary;

  /// No description provided for @uiSaveCanceled.
  ///
  /// In en, this message translates to:
  /// **'Save canceled'**
  String get uiSaveCanceled;

  /// No description provided for @uiDiscardTheCurrentChannelListAny.
  ///
  /// In en, this message translates to:
  /// **'Discard the current channel list? Any unsaved changes will be lost.'**
  String get uiDiscardTheCurrentChannelListAny;

  /// No description provided for @uiCloseTheCurrentChannelListAnd.
  ///
  /// In en, this message translates to:
  /// **'Close the current channel list and start {p0}?'**
  String uiCloseTheCurrentChannelListAnd(Object p0);

  /// No description provided for @uiANewBlankConfiguration.
  ///
  /// In en, this message translates to:
  /// **'a new blank configuration'**
  String get uiANewBlankConfiguration;

  /// No description provided for @uiReadingRadioSettingsDoNotDisconnect.
  ///
  /// In en, this message translates to:
  /// **'Reading radio settings - do not disconnect...'**
  String get uiReadingRadioSettingsDoNotDisconnect;

  /// No description provided for @uiSelectAChannelFirst.
  ///
  /// In en, this message translates to:
  /// **'Select a channel first'**
  String get uiSelectAChannelFirst;

  /// No description provided for @uiThisRadioHasFixedChannelLocations4.
  ///
  /// In en, this message translates to:
  /// **'This radio has fixed channel locations.'**
  String get uiThisRadioHasFixedChannelLocations4;

  /// No description provided for @uiAndFollowingChannelsMoveDownOne.
  ///
  /// In en, this message translates to:
  /// **'{p0} and following channels move down one slot.'**
  String uiAndFollowingChannelsMoveDownOne(Object p0);

  /// No description provided for @uiUseChannelAfterTheFinalChannel.
  ///
  /// In en, this message translates to:
  /// **'Use channel {p0} after the final channel.'**
  String uiUseChannelAfterTheFinalChannel(Object p0);

  /// No description provided for @uiTheCopiedChannelDoesNotFit.
  ///
  /// In en, this message translates to:
  /// **'The copied channel does not fit in this radio’s memory.'**
  String get uiTheCopiedChannelDoesNotFit;

  /// No description provided for @uiTheCopiedChannelsDoNotFit.
  ///
  /// In en, this message translates to:
  /// **'The copied channels do not fit starting at this row.'**
  String get uiTheCopiedChannelsDoNotFit;

  /// No description provided for @uiThisChannelContainsDataPastingWill.
  ///
  /// In en, this message translates to:
  /// **'This channel contains data. Pasting will replace it.'**
  String get uiThisChannelContainsDataPastingWill;

  /// No description provided for @uiContainsDataPastingWillReplaceIt.
  ///
  /// In en, this message translates to:
  /// **'“{p0}” contains data. Pasting will replace it.'**
  String uiContainsDataPastingWillReplaceIt(Object p0);

  /// No description provided for @uiLoadingRadioInstructions.
  ///
  /// In en, this message translates to:
  /// **'Loading radio instructions…'**
  String get uiLoadingRadioInstructions;

  /// No description provided for @uiRestoringChannelsFromTheStoredRadio.
  ///
  /// In en, this message translates to:
  /// **'Restoring channels from the stored radio image…'**
  String get uiRestoringChannelsFromTheStoredRadio;

  /// No description provided for @uiSomeChannelsWereNotWritten.
  ///
  /// In en, this message translates to:
  /// **'Some channels were not written'**
  String get uiSomeChannelsWereNotWritten;

  /// No description provided for @uiSomeChannelValuesWereAdjusted.
  ///
  /// In en, this message translates to:
  /// **'Some channel values were adjusted'**
  String get uiSomeChannelValuesWereAdjusted;

  /// No description provided for @uiTheWriteFinishedChannelsWereAdjusted.
  ///
  /// In en, this message translates to:
  /// **'The write finished. {p0} channels were adjusted and {p1} could not be written.'**
  String uiTheWriteFinishedChannelsWereAdjusted(Object p0, Object p1);

  /// No description provided for @uiTheCompatibleChannelsWereWrittenBut.
  ///
  /// In en, this message translates to:
  /// **'The compatible channels were written, but {p0} channels could not be written.'**
  String uiTheCompatibleChannelsWereWrittenBut(Object p0);

  /// No description provided for @uiTheWriteFinishedButNewchirpAdjusted.
  ///
  /// In en, this message translates to:
  /// **'The write finished, but NewChirp adjusted values the radio does not support.'**
  String get uiTheWriteFinishedButNewchirpAdjusted;

  /// No description provided for @uiChannelCouldNotBeWritten.
  ///
  /// In en, this message translates to:
  /// **'Channel {p0} {p1} could not be written: {p2}'**
  String uiChannelCouldNotBeWritten(Object p0, Object p1, Object p2);

  /// No description provided for @uiNameChangedFromTo.
  ///
  /// In en, this message translates to:
  /// **'name changed from \"{p0}\" to \"{p1}\"'**
  String uiNameChangedFromTo(Object p0, Object p1);

  /// No description provided for @uiLockedFieldSEverythingElseWas.
  ///
  /// In en, this message translates to:
  /// **'locked field(s): {p0}; everything else was written'**
  String uiLockedFieldSEverythingElseWas(Object p0);

  /// No description provided for @uiCancellingSafely.
  ///
  /// In en, this message translates to:
  /// **'Cancelling safely…'**
  String get uiCancellingSafely;

  /// No description provided for @uiUpdateAvailable.
  ///
  /// In en, this message translates to:
  /// **'Update available'**
  String get uiUpdateAvailable;

  /// No description provided for @uiNewchirpIsReady.
  ///
  /// In en, this message translates to:
  /// **'NewChirp {p0} is ready'**
  String uiNewchirpIsReady(Object p0);

  /// No description provided for @uiNewchirpIsAvailableYouAreRunning.
  ///
  /// In en, this message translates to:
  /// **'NewChirp {p0} is available. You are running {p1}.\n\nOpen the download page to get the right installer for your computer.'**
  String uiNewchirpIsAvailableYouAreRunning(Object p0, Object p1);

  /// No description provided for @uiYouAreRunningNewchirpCanDownload.
  ///
  /// In en, this message translates to:
  /// **'You are running {p0}. NewChirp can download and install {p1} for you, then reopen automatically. No visit to the website is required.'**
  String uiYouAreRunningNewchirpCanDownload(Object p0, Object p1);

  /// No description provided for @uiPreparingTheUpdateDownload.
  ///
  /// In en, this message translates to:
  /// **'Preparing the update download…'**
  String get uiPreparingTheUpdateDownload;

  /// No description provided for @uiDownloadingNewchirp.
  ///
  /// In en, this message translates to:
  /// **'Downloading NewChirp {p0}…'**
  String uiDownloadingNewchirp(Object p0);

  /// No description provided for @uiVerifiedStartingTheInstallerAndRestarting.
  ///
  /// In en, this message translates to:
  /// **'Verified. Starting the installer and restarting NewChirp…'**
  String get uiVerifiedStartingTheInstallerAndRestarting;

  /// No description provided for @uiNewchirpCouldNotPrepareTheUpdate.
  ///
  /// In en, this message translates to:
  /// **'NewChirp could not prepare the update.'**
  String get uiNewchirpCouldNotPrepareTheUpdate;

  /// No description provided for @uiDeleteChannel.
  ///
  /// In en, this message translates to:
  /// **'Delete channel {p0}?'**
  String uiDeleteChannel(Object p0);

  /// No description provided for @uiRepeaterRowsThroughStayInThe.
  ///
  /// In en, this message translates to:
  /// **'Repeater rows 15 through 22 stay in the radio. The name is cleared and the plain GMRS repeater frequency is put back.'**
  String get uiRepeaterRowsThroughStayInThe;

  /// No description provided for @uiThisChannelWillBeRemovedFrom.
  ///
  /// In en, this message translates to:
  /// **'This channel will be removed from the current configuration.'**
  String get uiThisChannelWillBeRemovedFrom;

  /// No description provided for @uiWillBeRemovedFromTheCurrent.
  ///
  /// In en, this message translates to:
  /// **'“{p0}” will be removed from the current configuration.'**
  String uiWillBeRemovedFromTheCurrent(Object p0);

  /// No description provided for @uiStoredImageReadyForYouCan.
  ///
  /// In en, this message translates to:
  /// **'Stored image ready for {p0}. You can write without reading again.'**
  String uiStoredImageReadyForYouCan(Object p0);

  /// No description provided for @uiARadioImageIsLoadedFrom.
  ///
  /// In en, this message translates to:
  /// **'A radio image is loaded from this session. Review all changes before writing.'**
  String get uiARadioImageIsLoadedFrom;

  /// No description provided for @uiClearSearchAndColumnFiltersTo.
  ///
  /// In en, this message translates to:
  /// **'Clear search and column filters to rearrange channels'**
  String get uiClearSearchAndColumnFiltersTo;

  /// No description provided for @uiRearrangeChannels.
  ///
  /// In en, this message translates to:
  /// **'Rearrange channels'**
  String get uiRearrangeChannels;

  /// No description provided for @uiPreparingFrequencyReference.
  ///
  /// In en, this message translates to:
  /// **'Preparing frequency reference…'**
  String get uiPreparingFrequencyReference;

  /// No description provided for @uiPrintingFrequencyReference.
  ///
  /// In en, this message translates to:
  /// **'Printing frequency reference…'**
  String get uiPrintingFrequencyReference;

  /// No description provided for @uiTheGmrsFrsReference.
  ///
  /// In en, this message translates to:
  /// **'The GMRS/FRS reference'**
  String get uiTheGmrsFrsReference;

  /// No description provided for @uiNewchirpChannelList.
  ///
  /// In en, this message translates to:
  /// **'NewChirp channel list'**
  String get uiNewchirpChannelList;

  /// No description provided for @uiNewchirpChannelList2.
  ///
  /// In en, this message translates to:
  /// **'NewChirp channel list: {p0}'**
  String uiNewchirpChannelList2(Object p0);

  /// No description provided for @uiPreparingChannelList.
  ///
  /// In en, this message translates to:
  /// **'Preparing channel list…'**
  String get uiPreparingChannelList;

  /// No description provided for @uiChannelList.
  ///
  /// In en, this message translates to:
  /// **'channel list'**
  String get uiChannelList;

  /// No description provided for @uiPrintingChannelList.
  ///
  /// In en, this message translates to:
  /// **'Printing channel list…'**
  String get uiPrintingChannelList;

  /// No description provided for @uiTheChannelList.
  ///
  /// In en, this message translates to:
  /// **'The channel list'**
  String get uiTheChannelList;

  /// No description provided for @uiNoPrintersFound.
  ///
  /// In en, this message translates to:
  /// **'No printers found'**
  String get uiNoPrintersFound;

  /// No description provided for @uiNewchirpCouldNotFindAnySystem.
  ///
  /// In en, this message translates to:
  /// **'NewChirp could not find any system printers, so the {p0} PDF was opened in your default PDF viewer. Use the viewer’s Print command to print it.'**
  String uiNewchirpCouldNotFindAnySystem(Object p0);

  /// No description provided for @uiThePdfWasOpenedInYour.
  ///
  /// In en, this message translates to:
  /// **'The {p0} PDF was opened in your default PDF viewer. Use the viewer’s Print command to print it.'**
  String uiThePdfWasOpenedInYour(Object p0);

  /// No description provided for @uiFrequencyMhz.
  ///
  /// In en, this message translates to:
  /// **'Frequency (MHz)'**
  String get uiFrequencyMhz;

  /// No description provided for @uiUseNotes.
  ///
  /// In en, this message translates to:
  /// **'Use / notes'**
  String get uiUseNotes;

  /// No description provided for @uiSharedMhzInterstitial.
  ///
  /// In en, this message translates to:
  /// **'Shared 462 MHz interstitial'**
  String get uiSharedMhzInterstitial;

  /// No description provided for @uiHandheldOnly.
  ///
  /// In en, this message translates to:
  /// **'Handheld only'**
  String get uiHandheldOnly;

  /// No description provided for @uiMainRepeaterOutput.
  ///
  /// In en, this message translates to:
  /// **'Main / repeater output'**
  String get uiMainRepeaterOutput;

  /// No description provided for @uiChMhzInterstitial.
  ///
  /// In en, this message translates to:
  /// **'Ch 1-7: 462 MHz interstitial'**
  String get uiChMhzInterstitial;

  /// No description provided for @uiChMhzInterstitial2.
  ///
  /// In en, this message translates to:
  /// **'Ch 8-14: 467 MHz interstitial'**
  String get uiChMhzInterstitial2;

  /// No description provided for @uiChMhzMain.
  ///
  /// In en, this message translates to:
  /// **'Ch 15-22: 462 MHz main'**
  String get uiChMhzMain;

  /// No description provided for @uiFrsPower.
  ///
  /// In en, this message translates to:
  /// **'FRS Power'**
  String get uiFrsPower;

  /// No description provided for @uiGmrsPower.
  ///
  /// In en, this message translates to:
  /// **'GMRS Power'**
  String get uiGmrsPower;

  /// No description provided for @uiInputYouTransmit.
  ///
  /// In en, this message translates to:
  /// **'Input - You Transmit'**
  String get uiInputYouTransmit;

  /// No description provided for @uiOutputYouListen.
  ///
  /// In en, this message translates to:
  /// **'Output - You Listen'**
  String get uiOutputYouListen;

  /// No description provided for @uiInputOutputMhz.
  ///
  /// In en, this message translates to:
  /// **'Input = output + 5 MHz'**
  String get uiInputOutputMhz;

  /// No description provided for @uiPreparingTransfer.
  ///
  /// In en, this message translates to:
  /// **'Preparing transfer...'**
  String get uiPreparingTransfer;

  /// No description provided for @uiWaitingForTheRadioToReport.
  ///
  /// In en, this message translates to:
  /// **'Waiting for the radio to report progress'**
  String get uiWaitingForTheRadioToReport;

  /// No description provided for @uiCompleteElapsed.
  ///
  /// In en, this message translates to:
  /// **'{p0}% complete  |  {p1} elapsed'**
  String uiCompleteElapsed(Object p0, Object p1);

  /// No description provided for @uiEnterAWholeNumber.
  ///
  /// In en, this message translates to:
  /// **'Enter a whole number'**
  String get uiEnterAWholeNumber;

  /// No description provided for @uiValueMustBeAtLeast.
  ///
  /// In en, this message translates to:
  /// **'Value must be at least {p0}'**
  String uiValueMustBeAtLeast(Object p0);

  /// No description provided for @uiValueMustBeAtMost.
  ///
  /// In en, this message translates to:
  /// **'Value must be at most {p0}'**
  String uiValueMustBeAtMost(Object p0);

  /// No description provided for @uiUseAtLeastCharacters.
  ///
  /// In en, this message translates to:
  /// **'Use at least {p0} characters'**
  String uiUseAtLeastCharacters(Object p0);

  /// No description provided for @uiUseAtMostCharacters.
  ///
  /// In en, this message translates to:
  /// **'Use at most {p0} characters'**
  String uiUseAtMostCharacters(Object p0);

  /// No description provided for @uiEnterAValidEmailAddress.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid email address.'**
  String get uiEnterAValidEmailAddress;

  /// No description provided for @uiCouldNotSendTheErrorReport.
  ///
  /// In en, this message translates to:
  /// **'Could not send the error report.'**
  String get uiCouldNotSendTheErrorReport;

  /// No description provided for @uiErrorReportSent.
  ///
  /// In en, this message translates to:
  /// **'Error report sent'**
  String get uiErrorReportSent;

  /// No description provided for @uiSubmitErrorReport.
  ///
  /// In en, this message translates to:
  /// **'Submit error report'**
  String get uiSubmitErrorReport;

  /// No description provided for @uiNoDiagnosticEventsRecorded.
  ///
  /// In en, this message translates to:
  /// **'No diagnostic events recorded.'**
  String get uiNoDiagnosticEventsRecorded;

  /// No description provided for @uiSendReport.
  ///
  /// In en, this message translates to:
  /// **'Send report'**
  String get uiSendReport;

  /// No description provided for @uiWaitingForMygmrsSignInYou.
  ///
  /// In en, this message translates to:
  /// **'Waiting for myGMRS sign-in. You can cancel this attempt.'**
  String get uiWaitingForMygmrsSignInYou;

  /// No description provided for @uiSignedInToMygmrsForThis.
  ///
  /// In en, this message translates to:
  /// **'Signed in to myGMRS for this session.'**
  String get uiSignedInToMygmrsForThis;

  /// No description provided for @uiMygmrsSignInCancelled.
  ///
  /// In en, this message translates to:
  /// **'myGMRS sign-in cancelled.'**
  String get uiMygmrsSignInCancelled;

  /// No description provided for @uiSigningOutOfMygmrs.
  ///
  /// In en, this message translates to:
  /// **'Signing out of myGMRS…'**
  String get uiSigningOutOfMygmrs;

  /// No description provided for @uiSignedOutOfMygmrs.
  ///
  /// In en, this message translates to:
  /// **'Signed out of myGMRS.'**
  String get uiSignedOutOfMygmrs;

  /// No description provided for @uiEnterBothLatitudeAndLongitudeOr.
  ///
  /// In en, this message translates to:
  /// **'Enter both latitude and longitude, or neither.'**
  String get uiEnterBothLatitudeAndLongitudeOr;

  /// No description provided for @uiLatitudeMustBeBetweenAnd.
  ///
  /// In en, this message translates to:
  /// **'Latitude must be between -90 and 90.'**
  String get uiLatitudeMustBeBetweenAnd;

  /// No description provided for @uiLongitudeMustBeBetweenAnd.
  ///
  /// In en, this message translates to:
  /// **'Longitude must be between -180 and 180.'**
  String get uiLongitudeMustBeBetweenAnd;

  /// No description provided for @uiUseEitherAZipCodeOr.
  ///
  /// In en, this message translates to:
  /// **'Use either a ZIP code or coordinates, not both.'**
  String get uiUseEitherAZipCodeOr;

  /// No description provided for @uiLatitudeAndLongitudeAreRequiredFor.
  ///
  /// In en, this message translates to:
  /// **'Latitude and longitude are required for a radius search.'**
  String get uiLatitudeAndLongitudeAreRequiredFor;

  /// No description provided for @uiRadiusMustBeGreaterThanZero.
  ///
  /// In en, this message translates to:
  /// **'Radius must be greater than zero.'**
  String get uiRadiusMustBeGreaterThanZero;

  /// No description provided for @uiSignInToMygmrsBeforeSearching.
  ///
  /// In en, this message translates to:
  /// **'Sign in to myGMRS before searching.'**
  String get uiSignInToMygmrsBeforeSearching;

  /// No description provided for @uiSigningInToMygmrs.
  ///
  /// In en, this message translates to:
  /// **'Signing in to myGMRS…'**
  String get uiSigningInToMygmrs;

  /// No description provided for @uiSearchingRepeaterbook.
  ///
  /// In en, this message translates to:
  /// **'Searching RepeaterBook…'**
  String get uiSearchingRepeaterbook;

  /// No description provided for @uiMygmrsRequiresAnActiveGmrsLicense2.
  ///
  /// In en, this message translates to:
  /// **'myGMRS requires an active GMRS license to expose repeater frequencies. Confirm that you are signed in with an eligible account. myGMRS text search does not understand county names; enter a 5-digit ZIP code for a nearby repeater search.'**
  String get uiMygmrsRequiresAnActiveGmrsLicense2;

  /// No description provided for @uiRepeaterbookMayNotHaveAGmrs.
  ///
  /// In en, this message translates to:
  /// **'RepeaterBook may not have a GMRS listing for this area yet.'**
  String get uiRepeaterbookMayNotHaveAGmrs;

  /// No description provided for @uiCoordinatesAreSearchedWithinTheSelected.
  ///
  /// In en, this message translates to:
  /// **'Coordinates are searched within the selected region.'**
  String get uiCoordinatesAreSearchedWithinTheSelected;

  /// No description provided for @uiCheckThatCountryAndRegionAre.
  ///
  /// In en, this message translates to:
  /// **'Check that Country and Region are correct.'**
  String get uiCheckThatCountryAndRegionAre;

  /// No description provided for @uiNoMatchingGmrsRepeatersWereFound.
  ///
  /// In en, this message translates to:
  /// **'No matching GMRS repeaters were found{p0}. {p1} {p2}'**
  String uiNoMatchingGmrsRepeatersWereFound(Object p0, Object p1, Object p2);

  /// No description provided for @uiOpenUse.
  ///
  /// In en, this message translates to:
  /// **'open use'**
  String get uiOpenUse;

  /// No description provided for @uiFmAnalog.
  ///
  /// In en, this message translates to:
  /// **'FM analog'**
  String get uiFmAnalog;

  /// No description provided for @uiNoMatchingRepeatersWereFoundZip.
  ///
  /// In en, this message translates to:
  /// **'No matching repeaters were found{p0}. ZIP searches default to 50 km; increase the radius or turn off active filters.{p1}'**
  String uiNoMatchingRepeatersWereFoundZip(Object p0, Object p1);

  /// No description provided for @uiNoMatchingRepeatersWereFoundCoordinates.
  ///
  /// In en, this message translates to:
  /// **'No matching repeaters were found{p0}. Coordinates are searched within the selected region. Increase the radius or turn off active filters.{p1}'**
  String uiNoMatchingRepeatersWereFoundCoordinates(Object p0, Object p1);

  /// No description provided for @uiNoMatchingRepeatersWereFoundCheck.
  ///
  /// In en, this message translates to:
  /// **'No matching repeaters were found{p0}. Check the selected region or increase the radius.{p1}'**
  String uiNoMatchingRepeatersWereFoundCheck(Object p0, Object p1);

  /// No description provided for @uiNoTone.
  ///
  /// In en, this message translates to:
  /// **'no tone'**
  String get uiNoTone;

  /// No description provided for @uiCancelSignIn.
  ///
  /// In en, this message translates to:
  /// **'Cancel sign-in'**
  String get uiCancelSignIn;

  /// No description provided for @uiSignOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get uiSignOut;

  /// No description provided for @uiSignInToMygmrs.
  ///
  /// In en, this message translates to:
  /// **'Sign in to myGMRS'**
  String get uiSignInToMygmrs;

  /// No description provided for @uiRepeaterNameCityOrZipCode.
  ///
  /// In en, this message translates to:
  /// **'Repeater name, city, or ZIP code'**
  String get uiRepeaterNameCityOrZipCode;

  /// No description provided for @uiCityZipCountyCallsignLandmarkOr.
  ///
  /// In en, this message translates to:
  /// **'City, ZIP, county, callsign, landmark, or notes'**
  String get uiCityZipCountyCallsignLandmarkOr;

  /// No description provided for @uiADigitZipSearchesNearbyRepeaters.
  ///
  /// In en, this message translates to:
  /// **'A 5-digit ZIP searches nearby repeaters. County names are not supported by myGMRS.'**
  String get uiADigitZipSearchesNearbyRepeaters;

  /// No description provided for @uiADigitZipSearchesRepeatersWithin.
  ///
  /// In en, this message translates to:
  /// **'A 5-digit ZIP searches repeaters within 50 km by default.'**
  String get uiADigitZipSearchesRepeatersWithin;

  /// No description provided for @uiAllCounties.
  ///
  /// In en, this message translates to:
  /// **'All counties'**
  String get uiAllCounties;

  /// No description provided for @uiSearchToPreviewRepeaterChannels.
  ///
  /// In en, this message translates to:
  /// **'Search to preview repeater channels.'**
  String get uiSearchToPreviewRepeaterChannels;

  /// No description provided for @uiShownOfLoadedDataFrom.
  ///
  /// In en, this message translates to:
  /// **'{p0} shown of {p1} loaded • Data from {p2}'**
  String uiShownOfLoadedDataFrom(Object p0, Object p1, Object p2);

  /// No description provided for @uiAddSelected.
  ///
  /// In en, this message translates to:
  /// **'Add selected'**
  String get uiAddSelected;

  /// No description provided for @uiAddSelected2.
  ///
  /// In en, this message translates to:
  /// **'Add {p0} selected'**
  String uiAddSelected2(Object p0);

  /// No description provided for @uiEditSelectedProperties.
  ///
  /// In en, this message translates to:
  /// **'Edit selected properties'**
  String get uiEditSelectedProperties;

  /// No description provided for @uiCopyChannels.
  ///
  /// In en, this message translates to:
  /// **'Copy {p0} channels'**
  String uiCopyChannels(Object p0);

  /// No description provided for @uiCutChannels.
  ///
  /// In en, this message translates to:
  /// **'Cut {p0} channels'**
  String uiCutChannels(Object p0);

  /// No description provided for @uiPasteChannels.
  ///
  /// In en, this message translates to:
  /// **'Paste {p0} channels'**
  String uiPasteChannels(Object p0);

  /// No description provided for @uiClearSelectedChannels.
  ///
  /// In en, this message translates to:
  /// **'Clear {p0} selected channels'**
  String uiClearSelectedChannels(Object p0);

  /// No description provided for @uiClearChannel.
  ///
  /// In en, this message translates to:
  /// **'Clear channel'**
  String get uiClearChannel;

  /// No description provided for @uiEmptyMemorySlotDoubleClickTo.
  ///
  /// In en, this message translates to:
  /// **'Empty memory slot. Double-click to create a channel.'**
  String get uiEmptyMemorySlotDoubleClickTo;

  /// No description provided for @uiDoubleClickToEditChannel.
  ///
  /// In en, this message translates to:
  /// **'Double-click to edit channel'**
  String get uiDoubleClickToEditChannel;

  /// No description provided for @uiDragToRearrangeChannel.
  ///
  /// In en, this message translates to:
  /// **'Drag to rearrange channel'**
  String get uiDragToRearrangeChannel;

  /// No description provided for @uiEmptySlot.
  ///
  /// In en, this message translates to:
  /// **'Empty slot'**
  String get uiEmptySlot;

  /// No description provided for @uiBugReportSent.
  ///
  /// In en, this message translates to:
  /// **'Bug report sent'**
  String get uiBugReportSent;

  /// No description provided for @uiSubmitBugReport2.
  ///
  /// In en, this message translates to:
  /// **'Submit bug report'**
  String get uiSubmitBugReport2;

  /// No description provided for @uiGiveEveryEntryANameBefore.
  ///
  /// In en, this message translates to:
  /// **'Give every {p0} entry a name before saving.'**
  String uiGiveEveryEntryANameBefore(Object p0);

  /// No description provided for @uiAddAChannelToCreate.
  ///
  /// In en, this message translates to:
  /// **'Add a channel to create'**
  String get uiAddAChannelToCreate;

  /// No description provided for @uiAChannelMayBelongToMore.
  ///
  /// In en, this message translates to:
  /// **'A channel may belong to more than one entry.'**
  String get uiAChannelMayBelongToMore;

  /// No description provided for @uiAChannelCanBelongToOne.
  ///
  /// In en, this message translates to:
  /// **'A channel can belong to one entry.'**
  String get uiAChannelCanBelongToOne;

  /// No description provided for @uiThisEmptyEntryIsTheRadio.
  ///
  /// In en, this message translates to:
  /// **'This empty entry is the radio’s spare bank or zone. Add a channel to create it.'**
  String get uiThisEmptyEntryIsTheRadio;

  /// No description provided for @uiChannelsSelected.
  ///
  /// In en, this message translates to:
  /// **'{p0} channels selected'**
  String uiChannelsSelected(Object p0);

  /// No description provided for @glossFrs.
  ///
  /// In en, this message translates to:
  /// **'Family Radio Service. A license-free UHF service in the United States.'**
  String get glossFrs;

  /// No description provided for @glossGmrs.
  ///
  /// In en, this message translates to:
  /// **'General Mobile Radio Service. A licensed UHF service in the United States.'**
  String get glossGmrs;

  /// No description provided for @glossRx.
  ///
  /// In en, this message translates to:
  /// **'Receive. The frequency or tone used when listening.'**
  String get glossRx;

  /// No description provided for @glossTx.
  ///
  /// In en, this message translates to:
  /// **'Transmit. The frequency or tone used when sending.'**
  String get glossTx;

  /// No description provided for @glossCtcss.
  ///
  /// In en, this message translates to:
  /// **'Continuous Tone-Coded Squelch System. A subaudible analog tone commonly called a PL tone.'**
  String get glossCtcss;

  /// No description provided for @glossTsql.
  ///
  /// In en, this message translates to:
  /// **'Tone squelch. Requires a matching CTCSS tone for both receive and transmit.'**
  String get glossTsql;

  /// No description provided for @glossDcs.
  ///
  /// In en, this message translates to:
  /// **'Digital-Coded Squelch System. A digital squelch code; NewChirp labels it DTCS.'**
  String get glossDcs;

  /// No description provided for @glossDtcs.
  ///
  /// In en, this message translates to:
  /// **'Digital-Coded Squelch System. A digital code used like a CTCSS tone to open a receiver or repeater.'**
  String get glossDtcs;

  /// No description provided for @glossDtcsPol.
  ///
  /// In en, this message translates to:
  /// **'DTCS polarity. Normal or inverted code polarity must match between the radio and repeater.'**
  String get glossDtcsPol;

  /// No description provided for @glossFm.
  ///
  /// In en, this message translates to:
  /// **'Frequency modulation. Standard analog voice mode.'**
  String get glossFm;

  /// No description provided for @glossNfm.
  ///
  /// In en, this message translates to:
  /// **'Narrowband FM. Uses less bandwidth and is common on FRS, GMRS, and busy repeater systems.'**
  String get glossNfm;

  /// No description provided for @glossAm.
  ///
  /// In en, this message translates to:
  /// **'Amplitude modulation. Used by some aircraft and amateur-radio channels.'**
  String get glossAm;

  /// No description provided for @glossDuplex.
  ///
  /// In en, this message translates to:
  /// **'Transmit/receive relationship. Simplex uses the same frequency; offsets and splits use different transmit frequencies.'**
  String get glossDuplex;

  /// No description provided for @glossOffset.
  ///
  /// In en, this message translates to:
  /// **'The frequency difference between receive and transmit.'**
  String get glossOffset;

  /// No description provided for @glossSplit.
  ///
  /// In en, this message translates to:
  /// **'Independent receive and transmit frequencies rather than a fixed offset.'**
  String get glossSplit;

  /// No description provided for @glossStep.
  ///
  /// In en, this message translates to:
  /// **'Tuning step size used when changing frequency.'**
  String get glossStep;

  /// No description provided for @glossScan.
  ///
  /// In en, this message translates to:
  /// **'Whether the channel is included in scanning or marked to skip.'**
  String get glossScan;

  /// No description provided for @glossBcl.
  ///
  /// In en, this message translates to:
  /// **'Busy Channel Lockout. Prevents transmitting when the channel is already in use.'**
  String get glossBcl;

  /// No description provided for @glossPttId.
  ///
  /// In en, this message translates to:
  /// **'Station identification sent at the beginning or end of a transmission, depending on the radio.'**
  String get glossPttId;

  /// No description provided for @glossSCode.
  ///
  /// In en, this message translates to:
  /// **'Signaling code selector. Chooses which stored PTT-ID or signaling code the channel uses.'**
  String get glossSCode;

  /// No description provided for @fileSaveWarning.
  ///
  /// In en, this message translates to:
  /// **'Saving this file does not write these changes to your radio. You must write your changes to the radio for them to take effect.'**
  String get fileSaveWarning;

  /// No description provided for @repeaterRangeIn.
  ///
  /// In en, this message translates to:
  /// **' in {location}'**
  String repeaterRangeIn(String location);

  /// No description provided for @repeaterRangeZip.
  ///
  /// In en, this message translates to:
  /// **' within {km} km of ZIP code {zip} in {location}'**
  String repeaterRangeZip(String km, String zip, String location);

  /// No description provided for @repeaterRangeCoords.
  ///
  /// In en, this message translates to:
  /// **' within {km} km of your coordinates in {location}'**
  String repeaterRangeCoords(String km, String location);

  /// No description provided for @repeaterFilterHint.
  ///
  /// In en, this message translates to:
  /// **' Active filters require {filters}; try turning them off.'**
  String repeaterFilterHint(String filters);

  /// No description provided for @listAnd.
  ///
  /// In en, this message translates to:
  /// **' and '**
  String get listAnd;

  /// No description provided for @occupiedBody.
  ///
  /// In en, this message translates to:
  /// **'{occupant} already uses channel {channel}. Choose how to place {moving}.'**
  String occupiedBody(String occupant, Object channel, String moving);

  /// No description provided for @anExistingChannel.
  ///
  /// In en, this message translates to:
  /// **'An existing channel'**
  String get anExistingChannel;

  /// No description provided for @thisChannel.
  ///
  /// In en, this message translates to:
  /// **'this channel'**
  String get thisChannel;

  /// No description provided for @channelsNeedAttention.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 channel needs attention before writing.} other{{count} channels need attention before writing.}}'**
  String channelsNeedAttention(int count);

  /// No description provided for @moreValidationIssues.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 more validation issue.} other{{count} more validation issues.}}'**
  String moreValidationIssues(int count);

  /// No description provided for @repeatersNoneImportable.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{{source} returned 1 matching repeater, but none could be imported.} other{{source} returned {count} matching repeaters, but none could be imported.}}'**
  String repeatersNoneImportable(int count, String source);

  /// No description provided for @countyCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 county} other{{count} counties}}'**
  String countyCount(int count);

  /// No description provided for @shortenNamesButton.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{Shorten 1 name to {limit}} other{Shorten {count} names to {limit}}}'**
  String shortenNamesButton(int count, int limit);

  /// No description provided for @shortenNamesTitle.
  ///
  /// In en, this message translates to:
  /// **'Shorten names to {limit} characters?'**
  String shortenNamesTitle(int limit);

  /// No description provided for @shortenNamesBody.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 channel name is longer than this radio allows. NewChirp will keep its first {limit} characters.} other{{count} channel names are longer than this radio allows. NewChirp will keep the first {limit} characters of each.}} You can undo this.'**
  String shortenNamesBody(int count, int limit);

  /// No description provided for @shortenNamesMore.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{and 1 more} other{and {count} more}}'**
  String shortenNamesMore(int count);

  /// No description provided for @shortenNamesDuplicates.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{1 shortened name will match another channel\'s name. Check it before writing.} other{{count} shortened names will match other channel names. Check them before writing.}}'**
  String shortenNamesDuplicates(int count);

  /// No description provided for @shortenNamesAction.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =1{Shorten 1 name} other{Shorten {count} names}}'**
  String shortenNamesAction(int count);
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
