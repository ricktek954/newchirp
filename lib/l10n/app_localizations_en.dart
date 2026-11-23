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
}
