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

  @override
  String get colBank => 'BANQUE';

  @override
  String get colName => 'NOM';

  @override
  String get colRxFrequency => 'FRÉQUENCE RX';

  @override
  String get colToneMode => 'MODE DE TONALITÉ';

  @override
  String get colTxTone => 'TONALITÉ TX';

  @override
  String get colRxTone => 'TONALITÉ RX';

  @override
  String get colDtcs => 'DTCS';

  @override
  String get colRxDtcs => 'DTCS RX';

  @override
  String get colDtcsPol => 'POL. DTCS';

  @override
  String get colDuplex => 'DUPLEX';

  @override
  String get colOffset => 'DÉCALAGE / FRÉQ. TX';

  @override
  String get colCrossMode => 'MODE CROISÉ';

  @override
  String get colMode => 'MODE';

  @override
  String get colStep => 'PAS';

  @override
  String get colPower => 'PUISSANCE';

  @override
  String get colScan => 'BALAYAGE';

  @override
  String get colComment => 'COMMENTAIRE';

  @override
  String get helpNumber =>
      'Numéro de canal ou emplacement mémoire enregistré dans la radio.';

  @override
  String get helpNumberMidland =>
      'Numéro de canal Midland. Les lignes de relais sont marquées RPTR.';

  @override
  String get helpBank =>
      'Banque ou zone d\'appartenance indiquée par la radio sélectionnée. Une bordure verte marque le début de chaque banque.';

  @override
  String get helpName => 'Nom du canal enregistré dans la mémoire de la radio.';

  @override
  String get helpRxFrequency =>
      'Fréquence de réception : la fréquence écoutée par la radio.';

  @override
  String get helpToneMode =>
      'Mode de squelch en réception/émission. Tone est le CTCSS, TSQL le squelch par tonalité, DTCS un code numérique, et Cross utilise des tonalités différentes.';

  @override
  String get helpTxTone =>
      'Tonalité CTCSS d\'émission en hertz. TSQL utilise la même tonalité CTCSS en émission et en réception.';

  @override
  String get helpRxTone =>
      'Tonalité CTCSS de réception en hertz. Réglez d\'abord le mode de tonalité sur TSQL ou sur un mode Cross adapté.';

  @override
  String get helpDtcs => 'Code de squelch numérique DTCS en émission.';

  @override
  String get helpRxDtcs => 'Code de squelch numérique DTCS en réception.';

  @override
  String get helpDtcsPol =>
      'Polarité DTCS : normale ou inversée en émission et en réception.';

  @override
  String get helpDuplex =>
      'Relation entre émission et réception. Simplex utilise une seule fréquence ; les décalages ou le mode split utilisent une autre fréquence d\'émission.';

  @override
  String get helpOffset =>
      'Décalage de fréquence, ou fréquence d\'émission indépendante en mode split.';

  @override
  String get helpCrossMode =>
      'Modes de tonalité/code distincts en réception et en émission, utilisés avec Cross.';

  @override
  String get helpMode =>
      'Modulation de la voix : FM, FM bande étroite ou AM selon la radio.';

  @override
  String get helpStep => 'Pas d\'accord en kHz.';

  @override
  String get helpPower => 'Niveau de puissance d\'émission sélectionné.';

  @override
  String get helpScan => 'Indique si le canal est inclus dans le balayage.';

  @override
  String get helpComment =>
      'Notes libres enregistrées avec le canal, si la radio le permet.';

  @override
  String get helpExtra =>
      'Réglage de canal propre à cette radio, fourni par le pilote CHIRP.';

  @override
  String get dragToReorder => 'Faites glisser pour réordonner la colonne';

  @override
  String get editorTitle => 'Détails du canal';

  @override
  String get editorSave => 'Enregistrer le canal';

  @override
  String editorBulkTitle(int count) {
    return 'Modifier $count canaux';
  }

  @override
  String editorBulkSave(int count) {
    return 'Mettre à jour $count';
  }

  @override
  String get tipAbbreviations => 'Abréviations et termes';

  @override
  String get tipResetRepeater => 'Réinitialiser le relais';

  @override
  String get tipDeleteChannel => 'Supprimer le canal';

  @override
  String get tipCloseEditor => 'Fermer l\'éditeur';

  @override
  String get fieldChannel => 'Canal';

  @override
  String get fieldLocation => 'Emplacement';

  @override
  String get fieldName => 'Nom';

  @override
  String get fieldReceiveChannel => 'Canal de réception';

  @override
  String get fieldReceiveFrequency => 'Fréquence de réception (MHz)';

  @override
  String get fieldDuplex => 'Duplex';

  @override
  String get fieldTxFrequency => 'Fréquence TX';

  @override
  String get fieldOffset => 'Décalage (MHz)';

  @override
  String get fieldToneMode => 'Mode de tonalité';

  @override
  String get fieldCrossMode => 'Mode croisé';

  @override
  String get fieldCtcssTone => 'Tonalité CTCSS (Hz)';

  @override
  String get fieldTransmitTone => 'Tonalité d\'émission (Hz)';

  @override
  String get fieldReceiveTone => 'Tonalité de réception (Hz)';

  @override
  String get fieldDtcsCode => 'Code DTCS';

  @override
  String get fieldTransmitDtcs => 'DTCS d\'émission';

  @override
  String get fieldReceiveDtcs => 'DTCS de réception';

  @override
  String get fieldDtcsPolarity => 'Polarité DTCS (TX / RX)';

  @override
  String get fieldMode => 'Mode';

  @override
  String get fieldStep => 'Pas (kHz)';

  @override
  String get fieldScan => 'Balayage';

  @override
  String get fieldTransmitPower => 'Puissance d\'émission';

  @override
  String get fieldComment => 'Commentaire';

  @override
  String get radioSpecificSettings => 'Réglages de canal propres à cette radio';

  @override
  String get gm32ReceiveOnly =>
      'Cette fréquence est en réception seule. La GM-32 émet sur les canaux GMRS.';

  @override
  String get choiceNone => 'Aucun';

  @override
  String get choiceToneSquelch => 'Squelch par tonalité';

  @override
  String get choiceSimplex => 'Simplex';

  @override
  String get choicePlusShift => 'Décalage +';

  @override
  String get choiceMinusShift => 'Décalage −';

  @override
  String get choiceSplit => 'Split';

  @override
  String get choiceTxOff => 'TX désactivée';

  @override
  String get choiceDtcsToNone => 'DTCS → Aucun';

  @override
  String get choiceNoneToDtcs => 'Aucun → DTCS';

  @override
  String get choiceNoneToTone => 'Aucun → Tone';

  @override
  String get choiceNormalNormal => 'Normale / Normale';

  @override
  String get choiceNormalReverse => 'Normale / Inversée';

  @override
  String get choiceReverseNormal => 'Inversée / Normale';

  @override
  String get choiceReverseReverse => 'Inversée / Inversée';

  @override
  String get choiceDigitalVoice => 'Voix numérique';
}
