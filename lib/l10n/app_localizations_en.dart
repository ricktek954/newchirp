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

  @override
  String get welcomeTitle => 'What would you like to do?';

  @override
  String get welcomeSubtitle =>
      'Open an existing CHIRP file or read channels directly from your radio.';

  @override
  String get welcomeLoadTitle => 'Load configuration';

  @override
  String get welcomeLoadBody =>
      'Open a CHIRP CSV or native image file and continue editing.';

  @override
  String get welcomeLoadHelp =>
      'Open a CHIRP-compatible CSV or native radio image. Native images retain the selected model and stored image needed for radio transfer.';

  @override
  String get welcomeReadTitle => 'Read channels from a radio';

  @override
  String get welcomeReadBody =>
      'Connect a programming cable and import the radio’s current channels.';

  @override
  String get welcomeConnect => 'Connect radio';

  @override
  String get welcomeReadHelp =>
      'Open the radio connection screen, choose your cable and exact model, then choose Read channels from the radio. Settings are read separately from the Radio settings page.';

  @override
  String get welcomeRepeatersTitle => 'Find nearby repeaters';

  @override
  String get welcomeRepeatersBody =>
      'Search RepeaterBook and add repeater channels.';

  @override
  String get welcomeRepeatersHelp =>
      'Search RepeaterBook for amateur and GMRS repeaters, preview matching repeaters, and add selected channels to the current library.';

  @override
  String get welcomeTip =>
      'Writing to a radio requires reading a matching image from it first. You can plan or edit a CSV anytime, but radio writes stay locked until a read completes.';

  @override
  String get updateCheckFailed => 'Couldn’t check for updates';

  @override
  String get updateCheckFailedHint =>
      'You can also download the latest version from newchirp.net.';

  @override
  String get aboutSubtitle =>
      'Application information and open-source licenses';

  @override
  String get freqRefTitle => 'Frequency Reference';

  @override
  String get freqRefUsSubtitle => 'United States Part 95 FRS/GMRS channel plan';

  @override
  String get settingsSubtitle =>
      'Radio-wide options exposed by the selected driver';

  @override
  String aboutTagline(String version) {
    return 'Desktop radio programmer · Version $version';
  }

  @override
  String get contributor => 'Contributor';

  @override
  String get chirpLayerTitle => 'CHIRP compatibility layer';

  @override
  String get chirpLayerBody1 =>
      'NewChirp uses the CHIRP driver tree for radio hardware compatibility. CHIRP copyright is held by its contributors, and CHIRP is free software licensed under the GNU General Public License, version 3 or (at your option) any later version.';

  @override
  String get chirpLayerBody2 =>
      'NewChirp also develops its own drivers for radios that do not yet have a CHIRP driver or whose existing CHIRP driver does not work correctly. These NewChirp-maintained drivers are released under GPLv3-or-later and are available for incorporation into upstream CHIRP under the same license, subject to CHIRP maintainer review and acceptance.';

  @override
  String chirpSource(String url) {
    return 'CHIRP project and source: $url';
  }

  @override
  String newchirpSource(String url) {
    return 'NewChirp project and source: $url';
  }

  @override
  String get licensesTitle => 'Open-source licenses';

  @override
  String get licensesBody =>
      'The complete CHIRP GPL text and pySerial, libusb, and Flutter dependency licenses are included with this application.';

  @override
  String get viewLicenses => 'View complete licenses';

  @override
  String get notAffiliated =>
      'NewChirp is an independent interface and is not affiliated with or endorsed by the CHIRP project.';

  @override
  String get settingsIntro =>
      'Adjust radio-wide options such as squelch, backlight, VOX, and other controls exposed by the selected CHIRP driver.';

  @override
  String get settingsNoModel =>
      'No radio model selected. Open Radio connection first.';

  @override
  String get settingsNoCable => 'No programming cable selected';

  @override
  String get settingsReadFromRadio => 'read from radio';

  @override
  String get settingsSnapshotAvailable => 'saved snapshot available';

  @override
  String get settingsLoading => 'Loading radio settings...';

  @override
  String get settingsUnsupportedTitle =>
      'This radio does not expose global settings';

  @override
  String get settingsUnsupportedBody =>
      'The selected CHIRP driver does not provide radio-wide settings. Per-channel settings are still available in the channel editor.';

  @override
  String get settingsLoadError => 'Could not load radio settings';

  @override
  String get settingsReadTitle => 'Read radio settings';

  @override
  String get settingsReadBodyConnected =>
      'Read the current settings directly from the connected radio. This refreshes the saved snapshot and settings only; the current channel list is not changed.';

  @override
  String get settingsReadBodyDisconnected =>
      'Select the programming cable and exact model on Radio connection, then read the radio to load its settings.';

  @override
  String get openRadioConnection => 'Open radio connection';

  @override
  String get settingsNotLoadedTitle => 'Settings have not loaded yet';

  @override
  String get settingsNotLoadedConnected =>
      'Read the current values from the connected radio, or use the saved radio snapshot for cached values.';

  @override
  String get settingsNotLoadedSnapshot =>
      'Use the saved radio snapshot to load cached values.';

  @override
  String get readSettingsFromRadio => 'Read current settings from radio';

  @override
  String get useSavedSnapshot => 'Use saved radio snapshot';

  @override
  String uiDefaultsComeFromChannelOnlyFields(Object p0) {
    return 'Defaults come from channel $p0. Only fields you change here are applied to all selected channels.';
  }

  @override
  String get uiSelectedChannelsNeedChanges => 'Selected channels need changes';

  @override
  String get uiBackToEditor => 'Back to editor';

  @override
  String uiUpdatedSelectedChannels(Object p0) {
    return 'Updated $p0 selected channels';
  }

  @override
  String uiConnectTheAndChooseItsPort(Object p0, Object p1) {
    return 'Connect the $p0 and choose its port to read $p1.';
  }

  @override
  String get uiBankAndZoneChangesAreReady =>
      'Bank and zone changes are ready. Write them with the channels.';

  @override
  String get uiCouldnTCompleteThatAction => 'Couldn’t complete that action';

  @override
  String get uiMoreInfo => 'More Info:';

  @override
  String get uiSubmitBugReport => 'Submit Bug Report';

  @override
  String get uiLoadExperimentalChirpModule => 'Load experimental CHIRP module?';

  @override
  String get uiChirpModulesAreExecutablePythonCode =>
      'CHIRP modules are executable Python code. NewChirp runs the module in a sandbox that blocks your home folder, other drives, and the network. The module can still use the selected radio and the files for this session.';

  @override
  String get uiOnlyLoadAModuleFromA =>
      'Only load a module from a source you trust. A bad module can still damage the radio. The module remains active only for this NewChirp session. Select the radio model and read the radio again before writing.';

  @override
  String get uiLoadModule => 'Load module';

  @override
  String uiMovedToChannel(Object p0, Object p1) {
    return 'Moved $p0 to channel $p1';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations =>
      'This radio has fixed channel locations, so empty slots cannot be inserted.';

  @override
  String uiInsertedAnEmptySlotBeforeChannel(Object p0) {
    return 'Inserted an empty slot before channel $p0';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations2 =>
      'This radio has fixed channel locations, so empty slots cannot be removed.';

  @override
  String uiRemovedEmptySlot(Object p0) {
    return 'Removed empty slot $p0';
  }

  @override
  String get uiRepeaterbookResults => 'RepeaterBook results';

  @override
  String get uiMacosBlockedTheSaveLocation => 'macOS blocked the save location';

  @override
  String get uiNewchirpDoesNotHavePermissionTo =>
      'NewChirp does not have permission to write to this folder. Choose another folder now, or allow NewChirp access in System Settings > Privacy & Security > Files and Folders.';

  @override
  String get uiChooseAnotherFolder => 'Choose another folder';

  @override
  String uiStart(Object p0) {
    return 'Start $p0?';
  }

  @override
  String get uiKeepCurrentList => 'Keep current list';

  @override
  String get uiDiscardAndContinue => 'Discard and continue';

  @override
  String uiMarineVhfTemplate(Object p0) {
    return '$p0 Marine VHF template';
  }

  @override
  String get uiStockChannels => 'stock channels';

  @override
  String get uiDiscardUnsavedSettingsChanges =>
      'Discard unsaved settings changes?';

  @override
  String get uiUsingTheSavedRadioSnapshotWill =>
      'Using the saved radio snapshot will replace the unsaved settings changes shown on this page.';

  @override
  String get uiUseSavedSnapshot => 'Use saved snapshot';

  @override
  String get uiReplaceUnsavedSettingsChanges =>
      'Replace unsaved settings changes?';

  @override
  String get uiReadingSettingsFromTheRadioWill =>
      'Reading settings from the radio will replace the unsaved settings changes shown on this page. The current channel list is not changed.';

  @override
  String get uiReadSettings => 'Read settings';

  @override
  String get uiWhereShouldTheNewChannelGo => 'Where should the new channel go?';

  @override
  String get uiAtTheEnd => 'At the end';

  @override
  String get uiBeforeTheSelectedChannel => 'Before the selected channel';

  @override
  String get uiAfterTheSelectedChannel => 'After the selected channel';

  @override
  String uiChannelAdded(Object p0) {
    return 'Channel $p0 added';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations3 =>
      'This radio has fixed channel locations. New channels can only be added after the final channel.';

  @override
  String uiOverwriteChannels(Object p0) {
    return 'Overwrite $p0 channels?';
  }

  @override
  String uiTheDestinationRangeThroughContainsChannels(
    Object p0,
    Object p1,
    Object p2,
  ) {
    return 'The destination range $p0 through $p1 contains $p2 channels with data. Pasting will replace them.';
  }

  @override
  String get uiOverwriteChannels2 => 'Overwrite channels';

  @override
  String uiOverwriteChannel(Object p0) {
    return 'Overwrite channel $p0?';
  }

  @override
  String get uiOverwriteChannel2 => 'Overwrite channel';

  @override
  String uiClearedChannelsUseCmdCtrlZ(Object p0) {
    return 'Cleared $p0 channels. Use Cmd/Ctrl+Z to undo.';
  }

  @override
  String uiStaysInTheRadioTheName(Object p0) {
    return '$p0 stays in the radio. The name is cleared and the plain repeater frequency is back.';
  }

  @override
  String uiAndMoreChannels(Object p0) {
    return '…and $p0 more channels.';
  }

  @override
  String get uiNamesAreConvertedOnlyWhenThe =>
      'Names are converted only when the selected radio requires it. Custom frequencies may require a channel outside the radio\'s locked memory range.';

  @override
  String get uiStopWritingTheRadio => 'Stop writing the radio?';

  @override
  String get uiTheRadioIsBeingWrittenNow =>
      'The radio is being written now. Some radios take a minute or two, and the elapsed time shows the write is still running. Stopping partway can leave part of the radio\'s memory half-written; it may then need a power cycle and a fresh write.';

  @override
  String get uiStopAnyway => 'Stop anyway';

  @override
  String get uiKeepWriting => 'Keep writing';

  @override
  String get uiLater => 'Later';

  @override
  String get uiOpenDownloadPage => 'Open download page';

  @override
  String get uiDownloadAndInstall => 'Download and install';

  @override
  String get uiFinishTheCurrentOperationFirst =>
      'Finish the current operation first';

  @override
  String get uiWaitForTheCurrentRadioOr =>
      'Wait for the current radio or file operation to finish before installing NewChirp.';

  @override
  String get uiSaveRadioSettingsFirst => 'Save radio settings first';

  @override
  String get uiYouHaveRadioSettingChangesThat =>
      'You have radio setting changes that have not been written. Save those settings before installing the update.';

  @override
  String get uiSaveYourChannelChangesFirst => 'Save your channel changes first';

  @override
  String get uiNewchirpWillCloseToInstallThe =>
      'NewChirp will close to install the update. Save the current channel list before continuing.';

  @override
  String get uiSaveAndContinue => 'Save and continue';

  @override
  String get uiInstallingNewchirpUpdate => 'Installing NewChirp update';

  @override
  String get uiNewchirpWillCloseAndReopenAutomatically =>
      'NewChirp will close and reopen automatically when the installer is ready.';

  @override
  String get uiUpdateCouldNotBeInstalled => 'Update could not be installed';

  @override
  String uiYouCanStillDownloadTheLatest(Object p0) {
    return '$p0\n\nYou can still download the latest version from newchirp.net.';
  }

  @override
  String get uiCouldnTOpenYourBrowser => 'Couldn’t open your browser';

  @override
  String uiNewchirpCouldNotStartTheBrowser(Object p0) {
    return 'NewChirp could not start the browser on this computer. Open this address yourself to get the update:\n\n$p0';
  }

  @override
  String get uiCopyLink => 'Copy link';

  @override
  String get uiYouReUpToDate => 'You’re up to date';

  @override
  String uiNewchirpIsTheLatestVersion(Object p0) {
    return 'NewChirp $p0 is the latest version.';
  }

  @override
  String uiChannelIsOccupied(Object p0) {
    return 'Channel $p0 is occupied';
  }

  @override
  String get uiReplace => 'Replace';

  @override
  String get uiSwap => 'Swap';

  @override
  String get uiMoveAndShift => 'Move and shift';

  @override
  String uiChannelsScanEnabledNeedAttention(Object p0, Object p1, Object p2) {
    return '$p0 channels · $p1 scan enabled · $p2 need attention';
  }

  @override
  String get uiReview => 'Review';

  @override
  String get uiNoRadioImageLoadedEditingAnd =>
      'No radio image loaded. Editing and CSV export work, but writing stays locked until you read from this radio.';

  @override
  String get uiChannelEditing => 'Channel editing';

  @override
  String get uiAddLetsYouPlaceANew =>
      'Add lets you place a new channel at the end, before the selected channel, or after it. Before and after shift following channels through the radio memory slots. Duplicate copies the selected row, and Delete removes it after confirmation. Double-click any row to edit all of its fields. Right-click a row to copy, cut, paste, duplicate, or clear it. Copying or cutting a multi-row selection copies the active channels as a block; paste places the block at the target row. Click selects one row. Shift-click selects a range, and Cmd/Ctrl-click toggles individual rows. Use Bulk edit to change channel properties on all selected rows; only fields you modify are applied. Right-click and choose Properties for the same editor. Drag the handle at the left edge of a row to move it; intervening channels shift through the same memory slots. Show empty slots keeps the radio memory layout visible; double-click an empty slot to create a channel there. Clear removes the selected row or all selected rows from the radio on the next write. Use Cmd/Ctrl+Z to undo and Cmd/Ctrl+Shift+Z to redo.';

  @override
  String get uiChooseAPrinter => 'Choose a printer';

  @override
  String get uiPrintJobSent => 'Print job sent';

  @override
  String uiWasSentTo(Object p0, Object p1) {
    return '$p0 was sent to $p1.';
  }

  @override
  String get uiUsFrsGmrs => 'US FRS / GMRS';

  @override
  String uiReferenceSourceVerifyCurrentNationalRules(Object p0) {
    return 'Reference source: $p0 Verify current national rules before transmitting.';
  }

  @override
  String get uiGmrsFrsFrequencyReference => 'GMRS & FRS Frequency Reference';

  @override
  String get uiUnitedStatesPartChannelPlanColor =>
      'United States Part 95 channel plan - color-coded by frequency band and power class.';

  @override
  String get uiRepeaterPairsGmrsOnly => 'Repeater Pairs (GMRS Only)';

  @override
  String get uiKeyNotes => 'Key notes';

  @override
  String get uiAllFrequenciesAreInMhzGmrs =>
      'All frequencies are in MHz. GMRS requires an FCC license; FRS is license-by-rule.\nGMRS mobile/base radios may not transmit on channels 8-14. Repeater inputs are GMRS-only.\nCommunity convention: Channel 20 (462.675 MHz) with CTCSS 141.3 Hz is often used as a travel/assistance channel.\nReference only - verify against current FCC Part 95 rules and your radio manual.';

  @override
  String get uiNoEditableOptionsInThisGroup =>
      'No editable options in this group.';

  @override
  String get uiKeepTheRadioPoweredOnAnd =>
      'Keep the radio powered on and the cable connected.';

  @override
  String uiThisSettingTypeIsNotSupported(Object p0) {
    return '$p0: this setting type is not supported yet.';
  }

  @override
  String get uiSearchAbbreviationsOrDefinitions =>
      'Search abbreviations or definitions';

  @override
  String get uiNoMatchingTerms => 'No matching terms.';

  @override
  String get uiThanksTheDiagnosticLogAndError =>
      'Thanks. The diagnostic log and error details were sent to the NewChirp developer.';

  @override
  String get uiYourEmail => 'Your email';

  @override
  String get uiUsedOnlyIfTheDeveloperNeeds =>
      'Used only if the developer needs more information.';

  @override
  String get uiWhatWereYouTryingToDo => 'What were you trying to do?';

  @override
  String get uiTheReportIncludesAppAndOperating =>
      'The report includes app and operating-system versions, the selected radio and serial port, and recent diagnostic events. Channel contents and loaded files are not logged.';

  @override
  String uiPreviewDiagnosticEvents(Object p0) {
    return 'Preview $p0 diagnostic events';
  }

  @override
  String uiFilterCounties(Object p0) {
    return 'Filter $p0 counties';
  }

  @override
  String get uiFindACounty => 'Find a county';

  @override
  String uiOfCounties(Object p0, Object p1) {
    return '$p0 of $p1 counties';
  }

  @override
  String get uiClearAll => 'Clear all';

  @override
  String get uiNoMatchingCounties => 'No matching counties.';

  @override
  String get uiNoCoordinatesAreAvailableForThese =>
      'No coordinates are available for these results.';

  @override
  String uiMappedTapAPinToSelect(Object p0) {
    return '$p0 mapped • tap a pin to select';
  }

  @override
  String get uiSearchARepeaterDirectoryAndAdd =>
      'Search a repeater directory and add selected channels to your current library. Verify repeater status and access before transmitting.';

  @override
  String get uiDirectory => 'Directory';

  @override
  String get uiMygmrsRequiresAnActiveGmrsLicense =>
      'myGMRS requires an active GMRS license for repeater frequencies. PL tones and rules require a Premium membership. This sign-in lasts until NewChirp closes.';

  @override
  String get uiCountry => 'Country';

  @override
  String get uiSortResults => 'Sort results';

  @override
  String get uiSourceOrder => 'Source order';

  @override
  String get uiFrequency => 'Frequency';

  @override
  String get uiCallsignName => 'Callsign / name';

  @override
  String get uiCity => 'City';

  @override
  String get uiCounty => 'County';

  @override
  String get uiService => 'Service';

  @override
  String get uiAmateurGmrs => 'Amateur + GMRS';

  @override
  String get uiAmateurHam => 'Amateur (ham)';

  @override
  String get uiClearRepeaterSearch => 'Clear repeater search';

  @override
  String get uiLatitudeOptional => 'Latitude (optional)';

  @override
  String get uiLongitudeOptional => 'Longitude (optional)';

  @override
  String get uiRadiusKm => 'Radius km';

  @override
  String get uiOpenRepeatersOnly => 'Open repeaters only';

  @override
  String get uiFmCapableOnly => 'FM-capable only';

  @override
  String get uiSearchAmateurRepeatersInstead =>
      'Search Amateur repeaters instead';

  @override
  String get uiFilterLoadedResults => 'Filter loaded results';

  @override
  String get uiCityCountyCallsignModeServiceOr =>
      'City, county, callsign, mode, service, or frequency';

  @override
  String get uiClearResultFilter => 'Clear result filter';

  @override
  String get uiList => 'List';

  @override
  String get uiMap => 'Map';

  @override
  String get uiSelectAll => 'Select all';

  @override
  String get uiClear => 'Clear';

  @override
  String get uiDataCourtesyOfRepeaterbookCom =>
      'Data courtesy of RepeaterBook.com.';

  @override
  String get uiDragToResize => 'Drag to resize';

  @override
  String get uiInsertEmptySlotBefore => 'Insert empty slot before';

  @override
  String get uiRemoveEmptySlot => 'Remove empty slot';

  @override
  String uiMove(Object p0) {
    return 'Move $p0';
  }

  @override
  String get uiDragRowsToRearrangeChannels => 'Drag rows to rearrange channels';

  @override
  String get uiFilter => 'Filter';

  @override
  String get uiNoMatchingChannels => 'No matching channels';

  @override
  String get uiWriteChannelsToRadio => 'Write channels to radio';

  @override
  String get uiThanksTheDiagnosticLogAndProblem =>
      'Thanks. The diagnostic log and problem details were sent to the NewChirp developer.';

  @override
  String get uiTheReportIncludesAppAndOperating2 =>
      'The report includes app and operating-system versions, the selected radio, firmware when available, serial port, and recent diagnostic events. Channel contents and loaded files are not logged.';

  @override
  String get uiSaveFile => 'Save file';

  @override
  String get uiDoNotShowMeThisMessage => 'Do not show me this message again';

  @override
  String get uiMarineVhfChannelTemplate => 'Marine VHF channel template';

  @override
  String get uiPlan => 'Plan';

  @override
  String uiSource(Object p0) {
    return 'Source: $p0';
  }

  @override
  String get uiTheChannelPlanIsSelectedBy =>
      'The channel plan is selected by regulatory region, not ZIP code. Marine channel assignments are national or international and do not change by postal code.';

  @override
  String get uiProgramShipTransmitFrequencies =>
      'Program ship transmit frequencies';

  @override
  String get uiReceiveOnlyIsTheSafeDefault =>
      'Receive-only is the safe default. Enable this only when the radio and installation are authorized for marine VHF transmission.';

  @override
  String get uiMostAmateurTransceiversAreNotType =>
      'Most amateur transceivers are not type-accepted for marine-band transmit. Prohibited and receive-only channels remain transmission-disabled.';

  @override
  String uiChannelsTransmitCapableReceiveOnly(Object p0, Object p1, Object p2) {
    return '$p0 channels: $p1 transmit-capable, $p2 receive-only.';
  }

  @override
  String get uiAllRowsWillBeAddedReceive =>
      'All rows will be added receive-only (Duplex \"off\"). The radio will beep and not transmit on them. Check the box above to program transmit frequencies.';

  @override
  String get uiContinue => 'Continue';

  @override
  String get uiType => 'Type';

  @override
  String get uiThisRadioDoesNotExposeEditable =>
      'This radio does not expose editable banks.';

  @override
  String get uiTheseBanksAreFixedByThe =>
      'These banks are fixed by the radio and are shown for reference.';

  @override
  String get uiUseTheseChanges => 'Use these changes';

  @override
  String get uiFindAChannel => 'Find a channel';

  @override
  String uiChannel(Object p0) {
    return 'Channel $p0';
  }

  @override
  String get uiLoadingRadioCatalog => 'Loading radio catalog…';

  @override
  String get uiActionFailed => 'Action failed';

  @override
  String uiMacosBlockedNewchirpFromWritingTo(Object p0) {
    return '$p0\n\nmacOS blocked NewChirp from writing to that folder. Choose a different save location, or allow NewChirp access under:\n\nSystem Settings > Privacy & Security > Files and Folders > NewChirp\n\nGrant access to Documents, then retry Save.';
  }

  @override
  String uiOnLinuxThisUsuallyMeansYour(Object p0) {
    return '$p0\n\nOn Linux, this usually means your user does not have permission to open the radio programming cable.\n\nFix it with:\n    sudo usermod -aG dialout \$USER\n\nThen log out and back in, reconnect the cable, and try again.\n\nFor the current terminal session only:\n    newgrp dialout';
  }

  @override
  String get uiMototrboCpsChannels => 'MOTOTRBO CPS 2.0 channels';

  @override
  String get uiCsvChannels => 'CSV channels';

  @override
  String get uiRefreshingRadioCatalog => 'Refreshing radio catalog…';

  @override
  String get uiThisChirpImage => 'this CHIRP image';

  @override
  String get uiNoEmptyChannelSlotIsAvailable =>
      'No empty channel slot is available.';

  @override
  String get uiNoEmptyChannelSlotsAreAvailable =>
      'No empty channel slots are available for this radio.';

  @override
  String get uiSavingChannelLibrary => 'Saving channel library…';

  @override
  String get uiSaveCanceled => 'Save canceled';

  @override
  String get uiDiscardTheCurrentChannelListAny =>
      'Discard the current channel list? Any unsaved changes will be lost.';

  @override
  String uiCloseTheCurrentChannelListAnd(Object p0) {
    return 'Close the current channel list and start $p0?';
  }

  @override
  String get uiANewBlankConfiguration => 'a new blank configuration';

  @override
  String get uiReadingRadioSettingsDoNotDisconnect =>
      'Reading radio settings - do not disconnect...';

  @override
  String get uiSelectAChannelFirst => 'Select a channel first';

  @override
  String get uiThisRadioHasFixedChannelLocations4 =>
      'This radio has fixed channel locations.';

  @override
  String uiAndFollowingChannelsMoveDownOne(Object p0) {
    return '$p0 and following channels move down one slot.';
  }

  @override
  String uiUseChannelAfterTheFinalChannel(Object p0) {
    return 'Use channel $p0 after the final channel.';
  }

  @override
  String get uiTheCopiedChannelDoesNotFit =>
      'The copied channel does not fit in this radio’s memory.';

  @override
  String get uiTheCopiedChannelsDoNotFit =>
      'The copied channels do not fit starting at this row.';

  @override
  String get uiThisChannelContainsDataPastingWill =>
      'This channel contains data. Pasting will replace it.';

  @override
  String uiContainsDataPastingWillReplaceIt(Object p0) {
    return '“$p0” contains data. Pasting will replace it.';
  }

  @override
  String get uiLoadingRadioInstructions => 'Loading radio instructions…';

  @override
  String get uiRestoringChannelsFromTheStoredRadio =>
      'Restoring channels from the stored radio image…';

  @override
  String get uiSomeChannelsWereNotWritten => 'Some channels were not written';

  @override
  String get uiSomeChannelValuesWereAdjusted =>
      'Some channel values were adjusted';

  @override
  String uiTheWriteFinishedChannelsWereAdjusted(Object p0, Object p1) {
    return 'The write finished. $p0 channels were adjusted and $p1 could not be written.';
  }

  @override
  String uiTheCompatibleChannelsWereWrittenBut(Object p0) {
    return 'The compatible channels were written, but $p0 channels could not be written.';
  }

  @override
  String get uiTheWriteFinishedButNewchirpAdjusted =>
      'The write finished, but NewChirp adjusted values the radio does not support.';

  @override
  String uiChannelCouldNotBeWritten(Object p0, Object p1, Object p2) {
    return 'Channel $p0 $p1 could not be written: $p2';
  }

  @override
  String uiNameChangedFromTo(Object p0, Object p1) {
    return 'name changed from \"$p0\" to \"$p1\"';
  }

  @override
  String uiLockedFieldSEverythingElseWas(Object p0) {
    return 'locked field(s): $p0; everything else was written';
  }

  @override
  String get uiCancellingSafely => 'Cancelling safely…';

  @override
  String get uiUpdateAvailable => 'Update available';

  @override
  String uiNewchirpIsReady(Object p0) {
    return 'NewChirp $p0 is ready';
  }

  @override
  String uiNewchirpIsAvailableYouAreRunning(Object p0, Object p1) {
    return 'NewChirp $p0 is available. You are running $p1.\n\nOpen the download page to get the right installer for your computer.';
  }

  @override
  String uiYouAreRunningNewchirpCanDownload(Object p0, Object p1) {
    return 'You are running $p0. NewChirp can download and install $p1 for you, then reopen automatically. No visit to the website is required.';
  }

  @override
  String get uiPreparingTheUpdateDownload => 'Preparing the update download…';

  @override
  String uiDownloadingNewchirp(Object p0) {
    return 'Downloading NewChirp $p0…';
  }

  @override
  String get uiVerifiedStartingTheInstallerAndRestarting =>
      'Verified. Starting the installer and restarting NewChirp…';

  @override
  String get uiNewchirpCouldNotPrepareTheUpdate =>
      'NewChirp could not prepare the update.';

  @override
  String uiDeleteChannel(Object p0) {
    return 'Delete channel $p0?';
  }

  @override
  String get uiRepeaterRowsThroughStayInThe =>
      'Repeater rows 15 through 22 stay in the radio. The name is cleared and the plain GMRS repeater frequency is put back.';

  @override
  String get uiThisChannelWillBeRemovedFrom =>
      'This channel will be removed from the current configuration.';

  @override
  String uiWillBeRemovedFromTheCurrent(Object p0) {
    return '“$p0” will be removed from the current configuration.';
  }

  @override
  String uiStoredImageReadyForYouCan(Object p0) {
    return 'Stored image ready for $p0. You can write without reading again.';
  }

  @override
  String get uiARadioImageIsLoadedFrom =>
      'A radio image is loaded from this session. Review all changes before writing.';

  @override
  String get uiClearSearchAndColumnFiltersTo =>
      'Clear search and column filters to rearrange channels';

  @override
  String get uiRearrangeChannels => 'Rearrange channels';

  @override
  String get uiPreparingFrequencyReference => 'Preparing frequency reference…';

  @override
  String get uiPrintingFrequencyReference => 'Printing frequency reference…';

  @override
  String get uiTheGmrsFrsReference => 'The GMRS/FRS reference';

  @override
  String get uiNewchirpChannelList => 'NewChirp channel list';

  @override
  String uiNewchirpChannelList2(Object p0) {
    return 'NewChirp channel list: $p0';
  }

  @override
  String get uiPreparingChannelList => 'Preparing channel list…';

  @override
  String get uiChannelList => 'channel list';

  @override
  String get uiPrintingChannelList => 'Printing channel list…';

  @override
  String get uiTheChannelList => 'The channel list';

  @override
  String get uiNoPrintersFound => 'No printers found';

  @override
  String uiNewchirpCouldNotFindAnySystem(Object p0) {
    return 'NewChirp could not find any system printers, so the $p0 PDF was opened in your default PDF viewer. Use the viewer’s Print command to print it.';
  }

  @override
  String uiThePdfWasOpenedInYour(Object p0) {
    return 'The $p0 PDF was opened in your default PDF viewer. Use the viewer’s Print command to print it.';
  }

  @override
  String get uiFrequencyMhz => 'Frequency (MHz)';

  @override
  String get uiUseNotes => 'Use / notes';

  @override
  String get uiSharedMhzInterstitial => 'Shared 462 MHz interstitial';

  @override
  String get uiHandheldOnly => 'Handheld only';

  @override
  String get uiMainRepeaterOutput => 'Main / repeater output';

  @override
  String get uiChMhzInterstitial => 'Ch 1-7: 462 MHz interstitial';

  @override
  String get uiChMhzInterstitial2 => 'Ch 8-14: 467 MHz interstitial';

  @override
  String get uiChMhzMain => 'Ch 15-22: 462 MHz main';

  @override
  String get uiFrsPower => 'FRS Power';

  @override
  String get uiGmrsPower => 'GMRS Power';

  @override
  String get uiInputYouTransmit => 'Input - You Transmit';

  @override
  String get uiOutputYouListen => 'Output - You Listen';

  @override
  String get uiInputOutputMhz => 'Input = output + 5 MHz';

  @override
  String get uiPreparingTransfer => 'Preparing transfer...';

  @override
  String get uiWaitingForTheRadioToReport =>
      'Waiting for the radio to report progress';

  @override
  String uiCompleteElapsed(Object p0, Object p1) {
    return '$p0% complete  |  $p1 elapsed';
  }

  @override
  String get uiEnterAWholeNumber => 'Enter a whole number';

  @override
  String uiValueMustBeAtLeast(Object p0) {
    return 'Value must be at least $p0';
  }

  @override
  String uiValueMustBeAtMost(Object p0) {
    return 'Value must be at most $p0';
  }

  @override
  String uiUseAtLeastCharacters(Object p0) {
    return 'Use at least $p0 characters';
  }

  @override
  String uiUseAtMostCharacters(Object p0) {
    return 'Use at most $p0 characters';
  }

  @override
  String get uiEnterAValidEmailAddress => 'Enter a valid email address.';

  @override
  String get uiCouldNotSendTheErrorReport => 'Could not send the error report.';

  @override
  String get uiErrorReportSent => 'Error report sent';

  @override
  String get uiSubmitErrorReport => 'Submit error report';

  @override
  String get uiNoDiagnosticEventsRecorded => 'No diagnostic events recorded.';

  @override
  String get uiSendReport => 'Send report';

  @override
  String get uiWaitingForMygmrsSignInYou =>
      'Waiting for myGMRS sign-in. You can cancel this attempt.';

  @override
  String get uiSignedInToMygmrsForThis =>
      'Signed in to myGMRS for this session.';

  @override
  String get uiMygmrsSignInCancelled => 'myGMRS sign-in cancelled.';

  @override
  String get uiSigningOutOfMygmrs => 'Signing out of myGMRS…';

  @override
  String get uiSignedOutOfMygmrs => 'Signed out of myGMRS.';

  @override
  String get uiEnterBothLatitudeAndLongitudeOr =>
      'Enter both latitude and longitude, or neither.';

  @override
  String get uiLatitudeMustBeBetweenAnd =>
      'Latitude must be between -90 and 90.';

  @override
  String get uiLongitudeMustBeBetweenAnd =>
      'Longitude must be between -180 and 180.';

  @override
  String get uiUseEitherAZipCodeOr =>
      'Use either a ZIP code or coordinates, not both.';

  @override
  String get uiLatitudeAndLongitudeAreRequiredFor =>
      'Latitude and longitude are required for a radius search.';

  @override
  String get uiRadiusMustBeGreaterThanZero =>
      'Radius must be greater than zero.';

  @override
  String get uiSignInToMygmrsBeforeSearching =>
      'Sign in to myGMRS before searching.';

  @override
  String get uiSigningInToMygmrs => 'Signing in to myGMRS…';

  @override
  String get uiSearchingRepeaterbook => 'Searching RepeaterBook…';

  @override
  String get uiMygmrsRequiresAnActiveGmrsLicense2 =>
      'myGMRS requires an active GMRS license to expose repeater frequencies. Confirm that you are signed in with an eligible account. myGMRS text search does not understand county names; enter a 5-digit ZIP code for a nearby repeater search.';

  @override
  String get uiRepeaterbookMayNotHaveAGmrs =>
      'RepeaterBook may not have a GMRS listing for this area yet.';

  @override
  String get uiCoordinatesAreSearchedWithinTheSelected =>
      'Coordinates are searched within the selected region.';

  @override
  String get uiCheckThatCountryAndRegionAre =>
      'Check that Country and Region are correct.';

  @override
  String uiNoMatchingGmrsRepeatersWereFound(Object p0, Object p1, Object p2) {
    return 'No matching GMRS repeaters were found$p0. $p1 $p2';
  }

  @override
  String get uiOpenUse => 'open use';

  @override
  String get uiFmAnalog => 'FM analog';

  @override
  String uiNoMatchingRepeatersWereFoundZip(Object p0, Object p1) {
    return 'No matching repeaters were found$p0. ZIP searches default to 50 km; increase the radius or turn off active filters.$p1';
  }

  @override
  String uiNoMatchingRepeatersWereFoundCoordinates(Object p0, Object p1) {
    return 'No matching repeaters were found$p0. Coordinates are searched within the selected region. Increase the radius or turn off active filters.$p1';
  }

  @override
  String uiNoMatchingRepeatersWereFoundCheck(Object p0, Object p1) {
    return 'No matching repeaters were found$p0. Check the selected region or increase the radius.$p1';
  }

  @override
  String get uiNoTone => 'no tone';

  @override
  String get uiCancelSignIn => 'Cancel sign-in';

  @override
  String get uiSignOut => 'Sign out';

  @override
  String get uiSignInToMygmrs => 'Sign in to myGMRS';

  @override
  String get uiRepeaterNameCityOrZipCode => 'Repeater name, city, or ZIP code';

  @override
  String get uiCityZipCountyCallsignLandmarkOr =>
      'City, ZIP, county, callsign, landmark, or notes';

  @override
  String get uiADigitZipSearchesNearbyRepeaters =>
      'A 5-digit ZIP searches nearby repeaters. County names are not supported by myGMRS.';

  @override
  String get uiADigitZipSearchesRepeatersWithin =>
      'A 5-digit ZIP searches repeaters within 50 km by default.';

  @override
  String get uiAllCounties => 'All counties';

  @override
  String get uiSearchToPreviewRepeaterChannels =>
      'Search to preview repeater channels.';

  @override
  String uiShownOfLoadedDataFrom(Object p0, Object p1, Object p2) {
    return '$p0 shown of $p1 loaded • Data from $p2';
  }

  @override
  String get uiAddSelected => 'Add selected';

  @override
  String uiAddSelected2(Object p0) {
    return 'Add $p0 selected';
  }

  @override
  String get uiEditSelectedProperties => 'Edit selected properties';

  @override
  String uiCopyChannels(Object p0) {
    return 'Copy $p0 channels';
  }

  @override
  String uiCutChannels(Object p0) {
    return 'Cut $p0 channels';
  }

  @override
  String uiPasteChannels(Object p0) {
    return 'Paste $p0 channels';
  }

  @override
  String uiClearSelectedChannels(Object p0) {
    return 'Clear $p0 selected channels';
  }

  @override
  String get uiClearChannel => 'Clear channel';

  @override
  String get uiEmptyMemorySlotDoubleClickTo =>
      'Empty memory slot. Double-click to create a channel.';

  @override
  String get uiDoubleClickToEditChannel => 'Double-click to edit channel';

  @override
  String get uiDragToRearrangeChannel => 'Drag to rearrange channel';

  @override
  String get uiEmptySlot => 'Empty slot';

  @override
  String get uiBugReportSent => 'Bug report sent';

  @override
  String get uiSubmitBugReport2 => 'Submit bug report';

  @override
  String uiGiveEveryEntryANameBefore(Object p0) {
    return 'Give every $p0 entry a name before saving.';
  }

  @override
  String get uiAddAChannelToCreate => 'Add a channel to create';

  @override
  String get uiAChannelMayBelongToMore =>
      'A channel may belong to more than one entry.';

  @override
  String get uiAChannelCanBelongToOne => 'A channel can belong to one entry.';

  @override
  String get uiThisEmptyEntryIsTheRadio =>
      'This empty entry is the radio’s spare bank or zone. Add a channel to create it.';

  @override
  String uiChannelsSelected(Object p0) {
    return '$p0 channels selected';
  }

  @override
  String get glossFrs =>
      'Family Radio Service. A license-free UHF service in the United States.';

  @override
  String get glossGmrs =>
      'General Mobile Radio Service. A licensed UHF service in the United States.';

  @override
  String get glossRx => 'Receive. The frequency or tone used when listening.';

  @override
  String get glossTx => 'Transmit. The frequency or tone used when sending.';

  @override
  String get glossCtcss =>
      'Continuous Tone-Coded Squelch System. A subaudible analog tone commonly called a PL tone.';

  @override
  String get glossTsql =>
      'Tone squelch. Requires a matching CTCSS tone for both receive and transmit.';

  @override
  String get glossDcs =>
      'Digital-Coded Squelch System. A digital squelch code; NewChirp labels it DTCS.';

  @override
  String get glossDtcs =>
      'Digital-Coded Squelch System. A digital code used like a CTCSS tone to open a receiver or repeater.';

  @override
  String get glossDtcsPol =>
      'DTCS polarity. Normal or inverted code polarity must match between the radio and repeater.';

  @override
  String get glossFm => 'Frequency modulation. Standard analog voice mode.';

  @override
  String get glossNfm =>
      'Narrowband FM. Uses less bandwidth and is common on FRS, GMRS, and busy repeater systems.';

  @override
  String get glossAm =>
      'Amplitude modulation. Used by some aircraft and amateur-radio channels.';

  @override
  String get glossDuplex =>
      'Transmit/receive relationship. Simplex uses the same frequency; offsets and splits use different transmit frequencies.';

  @override
  String get glossOffset =>
      'The frequency difference between receive and transmit.';

  @override
  String get glossSplit =>
      'Independent receive and transmit frequencies rather than a fixed offset.';

  @override
  String get glossStep => 'Tuning step size used when changing frequency.';

  @override
  String get glossScan =>
      'Whether the channel is included in scanning or marked to skip.';

  @override
  String get glossBcl =>
      'Busy Channel Lockout. Prevents transmitting when the channel is already in use.';

  @override
  String get glossPttId =>
      'Station identification sent at the beginning or end of a transmission, depending on the radio.';

  @override
  String get glossSCode =>
      'Signaling code selector. Chooses which stored PTT-ID or signaling code the channel uses.';

  @override
  String get fileSaveWarning =>
      'Saving this file does not write these changes to your radio. You must write your changes to the radio for them to take effect.';

  @override
  String repeaterRangeIn(String location) {
    return ' in $location';
  }

  @override
  String repeaterRangeZip(String km, String zip, String location) {
    return ' within $km km of ZIP code $zip in $location';
  }

  @override
  String repeaterRangeCoords(String km, String location) {
    return ' within $km km of your coordinates in $location';
  }

  @override
  String repeaterFilterHint(String filters) {
    return ' Active filters require $filters; try turning them off.';
  }

  @override
  String get listAnd => ' and ';

  @override
  String occupiedBody(String occupant, Object channel, String moving) {
    return '$occupant already uses channel $channel. Choose how to place $moving.';
  }

  @override
  String get anExistingChannel => 'An existing channel';

  @override
  String get thisChannel => 'this channel';

  @override
  String channelsNeedAttention(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count channels need attention before writing.',
      one: '1 channel needs attention before writing.',
    );
    return '$_temp0';
  }

  @override
  String moreValidationIssues(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count more validation issues.',
      one: '1 more validation issue.',
    );
    return '$_temp0';
  }

  @override
  String repeatersNoneImportable(int count, String source) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other:
          '$source returned $count matching repeaters, but none could be imported.',
      one: '$source returned 1 matching repeater, but none could be imported.',
    );
    return '$_temp0';
  }

  @override
  String countyCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count counties',
      one: '1 county',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesButton(int count, int limit) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'Shorten $count names to $limit',
      one: 'Shorten 1 name to $limit',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesTitle(int limit) {
    return 'Shorten names to $limit characters?';
  }

  @override
  String shortenNamesBody(int count, int limit) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other:
          '$count channel names are longer than this radio allows. NewChirp will keep the first $limit characters of each.',
      one:
          '1 channel name is longer than this radio allows. NewChirp will keep its first $limit characters.',
    );
    return '$_temp0 You can undo this.';
  }

  @override
  String shortenNamesMore(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'and $count more',
      one: 'and 1 more',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesDuplicates(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other:
          '$count shortened names will match other channel names. Check them before writing.',
      one:
          '1 shortened name will match another channel\'s name. Check it before writing.',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesAction(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'Shorten $count names',
      one: 'Shorten 1 name',
    );
    return '$_temp0';
  }

  @override
  String get uiUndecodedChannelsTitle => 'Some channels couldn\'t be decoded';

  @override
  String uiUndecodedChannelsBody(Object p0) {
    return 'NewChirp couldn\'t decode channel(s) $p0, so they are not in the list. They are left exactly as they are in the radio, and writes will not change them. Please send a report so the driver can be fixed; it includes the raw channel data.';
  }
}
