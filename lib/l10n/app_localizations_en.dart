// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get navRadioConnection => 'Radio connection';

  @override
  String get navChannelLibrary => 'Channel library';

  @override
  String get navRadioSettings => 'Radio settings';

  @override
  String get navFindRepeaters => 'Find repeaters';

  @override
  String get navFrequencyReference => 'Frequency reference';

  @override
  String get navAbout => 'About & licenses';

  @override
  String get sidebarDesktopProgrammer => 'DESKTOP RADIO PROGRAMMER';

  @override
  String get sidebarLeadProgrammer => 'Lead Programmer';

  @override
  String sidebarVersion(String version) {
    return 'Version $version';
  }

  @override
  String get languageLabel => 'Language';

  @override
  String get languageSystem => 'System default';

  @override
  String get languageBetaNote =>
      'Translations are in beta. Messages from radio drivers stay in English.';

  @override
  String get cancel => 'Cancel';

  @override
  String get ok => 'OK';

  @override
  String get apply => 'Apply';

  @override
  String get readReplaceTitle => 'Replace current channel list?';

  @override
  String get readReplaceBody =>
      'Reading channels from the radio will replace the current channel list. Save it as a CSV first if you want to keep it.';

  @override
  String get readChannels => 'Read channels';

  @override
  String get radioReadyToReceive => 'Radio is ready to receive';

  @override
  String get radioReady => 'Radio is ready';

  @override
  String beforeReading(String model) {
    return 'Before reading $model';
  }

  @override
  String beforeWriting(String model) {
    return 'Before writing $model';
  }

  @override
  String get readingProgress => 'Reading radio channels - do not disconnect...';

  @override
  String get writingProgress => 'Writing radio — do not disconnect…';

  @override
  String get writingSettingsProgress =>
      'Writing radio settings - do not disconnect...';

  @override
  String writeUnavailableTitle(String model) {
    return 'Writing to the $model isn\'t available yet';
  }

  @override
  String get writeUnavailableBody =>
      'NewChirp can read this radio, but writing stays off until a write has been tested and checked on a real radio. That keeps an untested write from damaging your radio\'s setup.\n\nYou can still read the radio, edit channels, and save or export them. If you can help test writing, send a bug report and say so.';

  @override
  String get incompatibleTitle => 'Some channels are incompatible';

  @override
  String incompatibleSummary(int invalid, int total) {
    return '$invalid of $total channels cannot be written to this radio.';
  }

  @override
  String incompatibleMore(int count) {
    return '…and $count more.';
  }

  @override
  String incompatibleSkipHint(int count) {
    return 'You can skip the incompatible channels and write the other $count.';
  }

  @override
  String get reviewChannels => 'Review channels';

  @override
  String get skipAndWriteRemaining => 'Skip and write remaining';

  @override
  String get writeChangesTitle => 'Write these radio changes?';

  @override
  String get writeChannelsTitle => 'Write these channels to the radio?';

  @override
  String writeConfirmBody(int count, String model, String port) {
    return 'This will program $count channels on $model through $port. Keep the radio connected and powered on.';
  }

  @override
  String get writeConfirmMappings =>
      'Bank and zone changes will be written too.';

  @override
  String writeConfirmIncompatible(int count) {
    return '$count incompatible channels will be left unchanged and listed after the write.';
  }

  @override
  String get writeConfirmUppercase =>
      'Lowercase channel names will be converted to uppercase because this radio only supports uppercase names.';

  @override
  String get writeToRadio => 'Write to radio';

  @override
  String applyTitle(String label) {
    return 'Apply $label';
  }

  @override
  String get applyIntro =>
      'Choose how to add these channels to the current list.';

  @override
  String get applyReplaceList => 'Replace the current channel list';

  @override
  String applyReplaceZone(String zone) {
    return 'Replace the channels in zone $zone';
  }

  @override
  String get applyReplaceListNote =>
      'Unsaved edits to the current list will be lost.';

  @override
  String get applyReplaceZoneNote =>
      'Other zones are not changed. Unsaved edits to this zone will be lost.';

  @override
  String get applyInsertAt => 'Insert starting at channel number';

  @override
  String applyInsertNote(int count) {
    return 'Channels in the $count-channel range will be overwritten.';
  }

  @override
  String get applyStartLabel => 'Starting channel number';

  @override
  String get applyStartError => 'Enter a channel number of 1 or higher.';

  @override
  String get settingsUnsaved => 'Unsaved settings changes';

  @override
  String get settingsMatchRadio =>
      'Settings match the values last read from the radio.';

  @override
  String get settingsMatchSnapshot =>
      'Settings match the saved radio snapshot.';

  @override
  String get discardChanges => 'Discard changes';

  @override
  String get connectRadioToWrite => 'Connect radio to write';

  @override
  String get writeSettingsToRadio => 'Write settings to radio';

  @override
  String get writeSettingsTitle => 'Write these radio settings?';

  @override
  String get writeSameSettingsTitle => 'Write the same settings again?';

  @override
  String writeSettingsBody(int count, String model, String port) {
    return 'This will write $count radio setting values to $model through $port. Keep the radio connected and powered on.';
  }

  @override
  String writeSameSettingsBody(String model, String port) {
    return 'Nothing has changed since the last read or write. NewChirp will write this radio snapshot, its settings and its channels, to $model through $port. Use this to program another radio of the same model. Keep the radio connected and powered on.';
  }

  @override
  String get writeSettingsButton => 'Write settings';

  @override
  String get colBank => 'BANK';

  @override
  String get colName => 'NAME';

  @override
  String get colRxFrequency => 'RX FREQUENCY';

  @override
  String get colToneMode => 'TONE MODE';

  @override
  String get colTxTone => 'TX TONE';

  @override
  String get colRxTone => 'RX TONE';

  @override
  String get colDtcs => 'DTCS';

  @override
  String get colRxDtcs => 'RX DTCS';

  @override
  String get colDtcsPol => 'DTCS POL';

  @override
  String get colDuplex => 'DUPLEX';

  @override
  String get colOffset => 'OFFSET / TX FREQ';

  @override
  String get colCrossMode => 'CROSS MODE';

  @override
  String get colMode => 'MODE';

  @override
  String get colStep => 'STEP';

  @override
  String get colPower => 'POWER';

  @override
  String get colScan => 'SCAN';

  @override
  String get colComment => 'COMMENT';

  @override
  String get helpNumber => 'Memory channel number or slot stored in the radio.';

  @override
  String get helpNumberMidland =>
      'Midland channel number. Repeater rows are labeled RPTR.';

  @override
  String get helpBank =>
      'Bank or zone membership reported by the selected radio. A green boundary marks the start of each bank.';

  @override
  String get helpName => 'Channel name stored in the radio memory.';

  @override
  String get helpRxFrequency =>
      'Receive frequency: the frequency the radio listens on.';

  @override
  String get helpToneMode =>
      'Receive/transmit squelch mode. Tone is CTCSS, TSQL is tone squelch, DTCS is a digital code, and Cross uses different tones.';

  @override
  String get helpTxTone =>
      'Transmit CTCSS tone in hertz. TSQL uses the same CTCSS tone for transmit and receive.';

  @override
  String get helpRxTone =>
      'Receive CTCSS tone in hertz. Set Tone Mode to TSQL or a matching Cross mode first.';

  @override
  String get helpDtcs => 'Transmit DTCS digital squelch code.';

  @override
  String get helpRxDtcs => 'Receive DTCS digital squelch code.';

  @override
  String get helpDtcsPol =>
      'DTCS polarity: normal or inverted for transmit and receive.';

  @override
  String get helpDuplex =>
      'Transmit/receive relationship. Simplex uses one frequency; offsets or split use different transmit frequencies.';

  @override
  String get helpOffset =>
      'Frequency offset, or the independent transmit frequency for split.';

  @override
  String get helpCrossMode =>
      'Separate receive and transmit tone/code modes used with Cross.';

  @override
  String get helpMode =>
      'Voice modulation: FM, narrowband FM, or AM depending on the radio.';

  @override
  String get helpStep => 'Tuning step size in kHz.';

  @override
  String get helpPower => 'Selected transmit power level.';

  @override
  String get helpScan => 'Whether the channel is included in scanning.';

  @override
  String get helpComment =>
      'Free-form notes stored with the channel when supported.';

  @override
  String get helpExtra =>
      'Radio-specific channel setting reported by the CHIRP driver.';

  @override
  String get dragToReorder => 'Drag to reorder column';

  @override
  String get editorTitle => 'Channel details';

  @override
  String get editorSave => 'Save channel';

  @override
  String editorBulkTitle(int count) {
    return 'Edit $count channels';
  }

  @override
  String editorBulkSave(int count) {
    return 'Update $count';
  }

  @override
  String get tipAbbreviations => 'Abbreviations & terms';

  @override
  String get tipResetRepeater => 'Reset repeater';

  @override
  String get tipDeleteChannel => 'Delete channel';

  @override
  String get tipCloseEditor => 'Close editor';

  @override
  String get fieldChannel => 'Channel';

  @override
  String get fieldLocation => 'Location';

  @override
  String get fieldName => 'Name';

  @override
  String get fieldReceiveChannel => 'Receive channel';

  @override
  String get fieldReceiveFrequency => 'Receive frequency (MHz)';

  @override
  String get fieldDuplex => 'Duplex';

  @override
  String get fieldTxFrequency => 'TX frequency';

  @override
  String get fieldOffset => 'Offset (MHz)';

  @override
  String get fieldToneMode => 'Tone mode';

  @override
  String get fieldCrossMode => 'Cross mode';

  @override
  String get fieldCtcssTone => 'CTCSS tone (Hz)';

  @override
  String get fieldTransmitTone => 'Transmit tone (Hz)';

  @override
  String get fieldReceiveTone => 'Receive tone (Hz)';

  @override
  String get fieldDtcsCode => 'DTCS code';

  @override
  String get fieldTransmitDtcs => 'Transmit DTCS';

  @override
  String get fieldReceiveDtcs => 'Receive DTCS';

  @override
  String get fieldDtcsPolarity => 'DTCS polarity (TX / RX)';

  @override
  String get fieldMode => 'Mode';

  @override
  String get fieldStep => 'Step (kHz)';

  @override
  String get fieldScan => 'Scan';

  @override
  String get fieldTransmitPower => 'Transmit power';

  @override
  String get fieldComment => 'Comment';

  @override
  String get radioSpecificSettings => 'Radio-specific channel settings';

  @override
  String get gm32ReceiveOnly =>
      'This frequency is receive-only. The GM-32 transmits on GMRS channels.';

  @override
  String get choiceNone => 'None';

  @override
  String get choiceToneSquelch => 'Tone squelch';

  @override
  String get choiceSimplex => 'Simplex';

  @override
  String get choicePlusShift => '+ shift';

  @override
  String get choiceMinusShift => '− shift';

  @override
  String get choiceSplit => 'Split';

  @override
  String get choiceTxOff => 'TX off';

  @override
  String get choiceDtcsToNone => 'DTCS → None';

  @override
  String get choiceNoneToDtcs => 'None → DTCS';

  @override
  String get choiceNoneToTone => 'None → Tone';

  @override
  String get choiceNormalNormal => 'Normal / Normal';

  @override
  String get choiceNormalReverse => 'Normal / Reverse';

  @override
  String get choiceReverseNormal => 'Reverse / Normal';

  @override
  String get choiceReverseReverse => 'Reverse / Reverse';

  @override
  String get choiceDigitalVoice => 'Digital voice';

  @override
  String get connIntro =>
      'Read channels from the radio first, edit them in the library, then write the verified image back.';

  @override
  String moduleLoaded(String name) {
    return 'Experimental CHIRP module loaded: $name';
  }

  @override
  String get unload => 'Unload';

  @override
  String get step1Title => 'Choose a programming cable';

  @override
  String get step1Help =>
      'NewChirp finds USB serial and mass-storage programming interfaces automatically. Choose the one that matches your radio connection. If nothing appears, connect the radio and press refresh.';

  @override
  String get programmingInterface => 'Programming interface';

  @override
  String get refreshInterfaces => 'Refresh interfaces';

  @override
  String get refreshHelp =>
      'Rescan the system for USB serial and mass-storage programming interfaces. If your radio is not listed, connect it and press refresh.';

  @override
  String get noInterface =>
      'No programming interface detected. Connect the radio and choose refresh.';

  @override
  String get step2Title => 'Choose the exact radio model';

  @override
  String get step2Help =>
      'Load the supported radio catalog and select the exact model. Using the wrong model can corrupt a radio. Programming cables do not identify the attached radio, so NewChirp does not guess the model. If a stored image already exists for this model, writing is unlocked without reading again.';

  @override
  String get loadCatalog => 'Load supported radio catalog';

  @override
  String get loadCatalogHelp =>
      'Fetch the list of radio models supported by the bundled CHIRP driver tree. Select the exact model before reading or writing.';

  @override
  String get step3Title => 'Transfer safely';

  @override
  String get step3Help =>
      'Read channels pulls the full memory image from the radio, replaces the current channel list, and stores the image for this model. Radio settings have a separate read action on the Radio settings page. Write sends the current channel list back using the stored image. Keep the radio connected and powered on during either transfer.';

  @override
  String get readChannelsFromRadio => 'Read channels from radio';

  @override
  String get imageNone =>
      'No image for this model yet. Read once to enable writing.';

  @override
  String imageStored(String model) {
    return 'Stored image for $model is ready. You can write without reading again.';
  }

  @override
  String get imageSession =>
      'A radio image was read this session. Review all changes before writing.';

  @override
  String get pickerSemanticsChoose => 'Choose radio model';

  @override
  String pickerSemanticsSelected(String model) {
    return 'Selected radio $model';
  }

  @override
  String get pickerLabel => 'Radio model';

  @override
  String pickerHint(int count) {
    return 'Choose from $count supported radios';
  }

  @override
  String get pickerTitle => 'Choose your radio';

  @override
  String get pickerSubtitle =>
      'Browse by manufacturer or search the complete catalog.';

  @override
  String get close => 'Close';

  @override
  String get pickerSearchHint =>
      'Search by manufacturer or model, e.g. Icom ID-52';

  @override
  String get clearSearch => 'Clear search';

  @override
  String get pickerNoMatch => 'No radio models match this search.';

  @override
  String pickerCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count radios',
      one: '1 radio',
    );
    return '$_temp0';
  }

  @override
  String get pickerAllVendors => 'All manufacturers';

  @override
  String get pickerRecent => 'Recent';

  @override
  String get selected => 'Selected';

  @override
  String get edited => '• Edited';

  @override
  String moduleActive(String name) {
    return 'Experimental CHIRP module: $name';
  }

  @override
  String get menuNew => 'New';

  @override
  String get newBlank => 'Blank configuration';

  @override
  String get newGmrs => 'GMRS starter template';

  @override
  String get newMarine => 'Marine VHF template';

  @override
  String get newRestoreStock => 'Restore stock channels';

  @override
  String get openChannelFile => 'Open channel file';

  @override
  String get loadModule => 'Load CHIRP driver module…';

  @override
  String get loadModuleShort => 'Load driver…';

  @override
  String get unloadModule => 'Unload CHIRP module';

  @override
  String get save => 'Save';

  @override
  String get saveAs => 'Save as…';

  @override
  String get printChannelList => 'Print channel list…';

  @override
  String get print => 'Print';

  @override
  String get help => 'Help';

  @override
  String get reportProblem => 'Report a problem…';

  @override
  String get checkingUpdates => 'Checking for updates...';

  @override
  String get checkUpdates => 'Check for updates';

  @override
  String get showSummary => 'Show channel summary';

  @override
  String get hideSummary => 'Hide channel summary to show more channels';

  @override
  String get metricChannels => 'Channels';

  @override
  String get metricScan => 'Scan enabled';

  @override
  String get metricAttention => 'Needs attention';

  @override
  String get editBanksZones => 'Edit banks / zones';

  @override
  String get banksZonesTitle => 'Banks and zones';

  @override
  String get banksZonesHelp =>
      'Use this editor to rename zones or banks and choose which channel memories belong to each one. Some radios allow a channel in multiple zones. An empty “New zone” entry is created by adding a channel to it. Changes are written with the channels; review them before writing because membership follows the channel memory number.';

  @override
  String get radioSection => 'Radio section';

  @override
  String zoneChannelCount(String name, int count) {
    return '$name ($count channels)';
  }

  @override
  String get radioSectionsTitle => 'Radio sections';

  @override
  String get radioSectionsHelp =>
      'This radio exposes separate channel sections or subdevices. Choose a section to view and edit its channels. Writing preserves the other sections in the saved radio image. Banks and zones are edited separately.';

  @override
  String get search => 'Search';

  @override
  String get searchHint => 'Search name, frequency, or note';

  @override
  String get clearChannelSearch => 'Clear channel search';

  @override
  String bulkEditTip(int count) {
    return 'Bulk edit $count selected channels';
  }

  @override
  String clearSelectedTip(int count) {
    return 'Clear $count selected channels';
  }

  @override
  String get duplicateChannel => 'Duplicate channel';

  @override
  String get addChannel => 'Add channel';

  @override
  String get slots => 'Slots';

  @override
  String get showEmptySlotsTip =>
      'Show every memory slot, including empty ones';

  @override
  String get clearColumnFilters => 'Clear column filters';

  @override
  String editSelected(int count) {
    return 'Edit $count selected';
  }

  @override
  String get duplicate => 'Duplicate';

  @override
  String get showEmptySlots => 'Show empty slots';

  @override
  String get clearFilters => 'Clear filters';

  @override
  String get openShort => 'Open…';
}
