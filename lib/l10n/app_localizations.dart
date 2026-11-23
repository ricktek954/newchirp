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
