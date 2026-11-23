// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for French (`fr`).
class AppLocalizationsFr extends AppLocalizations {
  AppLocalizationsFr([String locale = 'fr']) : super(locale);

  @override
  String get navRadioConnection => 'Connexion de la radio';

  @override
  String get navChannelLibrary => 'Bibliothèque de canaux';

  @override
  String get navRadioSettings => 'Réglages de la radio';

  @override
  String get navFindRepeaters => 'Trouver des relais';

  @override
  String get navFrequencyReference => 'Référence des fréquences';

  @override
  String get navAbout => 'À propos et licences';

  @override
  String get sidebarDesktopProgrammer => 'PROGRAMMATEUR RADIO DE BUREAU';

  @override
  String get sidebarLeadProgrammer => 'Programmeur principal';

  @override
  String sidebarVersion(String version) {
    return 'Version $version';
  }

  @override
  String get languageLabel => 'Langue';

  @override
  String get languageSystem => 'Langue du système';

  @override
  String get languageBetaNote =>
      'Les traductions sont en bêta. Les messages des pilotes radio restent en anglais.';

  @override
  String get cancel => 'Annuler';

  @override
  String get ok => 'OK';

  @override
  String get apply => 'Appliquer';

  @override
  String get readReplaceTitle => 'Remplacer la liste de canaux actuelle ?';

  @override
  String get readReplaceBody =>
      'La lecture des canaux de la radio remplacera la liste de canaux actuelle. Enregistrez-la d\'abord en CSV si vous voulez la conserver.';

  @override
  String get readChannels => 'Lire les canaux';

  @override
  String get radioReadyToReceive => 'La radio est prête à recevoir';

  @override
  String get radioReady => 'La radio est prête';

  @override
  String beforeReading(String model) {
    return 'Avant de lire $model';
  }

  @override
  String beforeWriting(String model) {
    return 'Avant d\'écrire dans $model';
  }

  @override
  String get readingProgress =>
      'Lecture des canaux de la radio : ne la déconnectez pas...';

  @override
  String get writingProgress =>
      'Écriture dans la radio : ne la déconnectez pas…';

  @override
  String get writingSettingsProgress =>
      'Écriture des réglages de la radio : ne la déconnectez pas...';

  @override
  String writeUnavailableTitle(String model) {
    return 'L\'écriture dans $model n\'est pas encore disponible';
  }

  @override
  String get writeUnavailableBody =>
      'NewChirp peut lire cette radio, mais l\'écriture reste désactivée tant qu\'elle n\'a pas été testée et vérifiée sur une vraie radio. Cela évite qu\'une écriture non testée n\'endommage la configuration de votre radio.\n\nVous pouvez toujours lire la radio, modifier les canaux et les enregistrer ou les exporter. Si vous pouvez aider à tester l\'écriture, envoyez un rapport de bogue en le précisant.';

  @override
  String get incompatibleTitle => 'Certains canaux sont incompatibles';

  @override
  String incompatibleSummary(int invalid, int total) {
    return '$invalid canaux sur $total ne peuvent pas être écrits dans cette radio.';
  }

  @override
  String incompatibleMore(int count) {
    return '…et $count de plus.';
  }

  @override
  String incompatibleSkipHint(int count) {
    return 'Vous pouvez ignorer les canaux incompatibles et écrire les $count autres.';
  }

  @override
  String get reviewChannels => 'Vérifier les canaux';

  @override
  String get skipAndWriteRemaining => 'Ignorer et écrire le reste';

  @override
  String get writeChangesTitle => 'Écrire ces modifications dans la radio ?';

  @override
  String get writeChannelsTitle => 'Écrire ces canaux dans la radio ?';

  @override
  String writeConfirmBody(int count, String model, String port) {
    return '$count canaux vont être programmés dans $model via $port. Gardez la radio connectée et allumée.';
  }

  @override
  String get writeConfirmMappings =>
      'Les modifications des banques et des zones seront aussi écrites.';

  @override
  String writeConfirmIncompatible(int count) {
    return '$count canaux incompatibles ne seront pas modifiés et seront listés après l\'écriture.';
  }

  @override
  String get writeConfirmUppercase =>
      'Les noms de canaux en minuscules seront convertis en majuscules, car cette radio n\'accepte que les majuscules.';

  @override
  String get writeToRadio => 'Écrire dans la radio';

  @override
  String applyTitle(String label) {
    return 'Appliquer $label';
  }

  @override
  String get applyIntro =>
      'Choisissez comment ajouter ces canaux à la liste actuelle.';

  @override
  String get applyReplaceList => 'Remplacer la liste de canaux actuelle';

  @override
  String applyReplaceZone(String zone) {
    return 'Remplacer les canaux de la zone $zone';
  }

  @override
  String get applyReplaceListNote =>
      'Les modifications non enregistrées de la liste actuelle seront perdues.';

  @override
  String get applyReplaceZoneNote =>
      'Les autres zones ne changent pas. Les modifications non enregistrées de cette zone seront perdues.';

  @override
  String get applyInsertAt => 'Insérer à partir du numéro de canal';

  @override
  String applyInsertNote(int count) {
    return 'Les canaux de la plage de $count canaux seront écrasés.';
  }

  @override
  String get applyStartLabel => 'Numéro de canal de départ';

  @override
  String get applyStartError =>
      'Saisissez un numéro de canal égal ou supérieur à 1.';

  @override
  String get settingsUnsaved => 'Modifications de réglages non enregistrées';

  @override
  String get settingsMatchRadio =>
      'Les réglages correspondent aux dernières valeurs lues dans la radio.';

  @override
  String get settingsMatchSnapshot =>
      'Les réglages correspondent à la copie enregistrée de la radio.';

  @override
  String get discardChanges => 'Annuler les modifications';

  @override
  String get connectRadioToWrite => 'Connectez la radio pour écrire';

  @override
  String get writeSettingsToRadio => 'Écrire les réglages dans la radio';

  @override
  String get writeSettingsTitle => 'Écrire ces réglages dans la radio ?';

  @override
  String get writeSameSettingsTitle => 'Écrire à nouveau les mêmes réglages ?';

  @override
  String writeSettingsBody(int count, String model, String port) {
    return '$count valeurs de réglages vont être écrites dans $model via $port. Gardez la radio connectée et allumée.';
  }

  @override
  String writeSameSettingsBody(String model, String port) {
    return 'Rien n\'a changé depuis la dernière lecture ou écriture. NewChirp va écrire cette copie de la radio, ses réglages et ses canaux, dans $model via $port. Utilisez cette option pour programmer une autre radio du même modèle. Gardez la radio connectée et allumée.';
  }

  @override
  String get writeSettingsButton => 'Écrire les réglages';
}
