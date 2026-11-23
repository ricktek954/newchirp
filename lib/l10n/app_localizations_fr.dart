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

  @override
  String get connIntro =>
      'Lisez d\'abord les canaux de la radio, modifiez-les dans la bibliothèque, puis réécrivez l\'image vérifiée.';

  @override
  String moduleLoaded(String name) {
    return 'Module CHIRP expérimental chargé : $name';
  }

  @override
  String get unload => 'Décharger';

  @override
  String get step1Title => 'Choisissez un câble de programmation';

  @override
  String get step1Help =>
      'NewChirp détecte automatiquement les interfaces de programmation USB série et de stockage de masse. Choisissez celle qui correspond à la connexion de votre radio. Si rien n\'apparaît, connectez la radio et appuyez sur actualiser.';

  @override
  String get programmingInterface => 'Interface de programmation';

  @override
  String get refreshInterfaces => 'Actualiser les interfaces';

  @override
  String get refreshHelp =>
      'Relance la recherche des interfaces de programmation USB série et de stockage de masse. Si votre radio n\'apparaît pas, connectez-la et appuyez sur actualiser.';

  @override
  String get noInterface =>
      'Aucune interface de programmation détectée. Connectez la radio et choisissez actualiser.';

  @override
  String get step2Title => 'Choisissez le modèle exact de radio';

  @override
  String get step2Help =>
      'Chargez le catalogue des radios prises en charge et sélectionnez le modèle exact. Un mauvais modèle peut corrompre une radio. Les câbles de programmation n\'identifient pas la radio branchée, donc NewChirp ne devine pas le modèle. Si une image enregistrée existe déjà pour ce modèle, l\'écriture est possible sans relire la radio.';

  @override
  String get loadCatalog => 'Charger le catalogue des radios prises en charge';

  @override
  String get loadCatalogHelp =>
      'Récupère la liste des modèles de radio pris en charge par les pilotes CHIRP fournis. Sélectionnez le modèle exact avant de lire ou d\'écrire.';

  @override
  String get step3Title => 'Transférez en toute sécurité';

  @override
  String get step3Help =>
      'Lire les canaux récupère l\'image mémoire complète de la radio, remplace la liste de canaux actuelle et enregistre l\'image pour ce modèle. Les réglages de la radio se lisent séparément, sur la page Réglages de la radio. Écrire renvoie la liste de canaux actuelle en utilisant l\'image enregistrée. Gardez la radio connectée et allumée pendant chaque transfert.';

  @override
  String get readChannelsFromRadio => 'Lire les canaux de la radio';

  @override
  String get imageNone =>
      'Pas encore d\'image pour ce modèle. Lisez la radio une fois pour activer l\'écriture.';

  @override
  String imageStored(String model) {
    return 'L\'image enregistrée de $model est prête. Vous pouvez écrire sans relire la radio.';
  }

  @override
  String get imageSession =>
      'Une image de la radio a été lue pendant cette session. Vérifiez toutes les modifications avant d\'écrire.';

  @override
  String get pickerSemanticsChoose => 'Choisir le modèle de radio';

  @override
  String pickerSemanticsSelected(String model) {
    return 'Radio sélectionnée : $model';
  }

  @override
  String get pickerLabel => 'Modèle de radio';

  @override
  String pickerHint(int count) {
    return 'Choisissez parmi $count radios prises en charge';
  }

  @override
  String get pickerTitle => 'Choisissez votre radio';

  @override
  String get pickerSubtitle =>
      'Parcourez par fabricant ou cherchez dans le catalogue complet.';

  @override
  String get close => 'Fermer';

  @override
  String get pickerSearchHint =>
      'Cherchez par fabricant ou modèle, p. ex. Icom ID-52';

  @override
  String get clearSearch => 'Effacer la recherche';

  @override
  String get pickerNoMatch =>
      'Aucun modèle de radio ne correspond à cette recherche.';

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
  String get pickerAllVendors => 'Tous les fabricants';

  @override
  String get pickerRecent => 'Récents';

  @override
  String get selected => 'Sélectionnée';

  @override
  String get edited => '• Modifié';

  @override
  String moduleActive(String name) {
    return 'Module CHIRP expérimental : $name';
  }

  @override
  String get menuNew => 'Nouveau';

  @override
  String get newBlank => 'Configuration vierge';

  @override
  String get newGmrs => 'Modèle de départ GMRS';

  @override
  String get newMarine => 'Modèle VHF marine';

  @override
  String get newRestoreStock => 'Restaurer les canaux d\'usine';

  @override
  String get openChannelFile => 'Ouvrir un fichier de canaux';

  @override
  String get loadModule => 'Charger un module de pilote CHIRP…';

  @override
  String get loadModuleShort => 'Charger un pilote…';

  @override
  String get unloadModule => 'Décharger le module CHIRP';

  @override
  String get save => 'Enregistrer';

  @override
  String get saveAs => 'Enregistrer sous…';

  @override
  String get printChannelList => 'Imprimer la liste des canaux…';

  @override
  String get print => 'Imprimer';

  @override
  String get help => 'Aide';

  @override
  String get reportProblem => 'Signaler un problème…';

  @override
  String get checkingUpdates => 'Recherche de mises à jour...';

  @override
  String get checkUpdates => 'Rechercher des mises à jour';

  @override
  String get showSummary => 'Afficher le résumé des canaux';

  @override
  String get hideSummary => 'Masquer le résumé pour afficher plus de canaux';

  @override
  String get metricChannels => 'Canaux';

  @override
  String get metricScan => 'Balayage activé';

  @override
  String get metricAttention => 'À vérifier';

  @override
  String get editBanksZones => 'Modifier banques / zones';

  @override
  String get banksZonesTitle => 'Banques et zones';

  @override
  String get banksZonesHelp =>
      'Utilisez cet éditeur pour renommer les zones ou les banques et choisir les mémoires de canaux de chacune. Certaines radios acceptent un canal dans plusieurs zones. Une entrée vide « Nouvelle zone » est créée en y ajoutant un canal. Les modifications sont écrites avec les canaux ; vérifiez-les avant d\'écrire, car l\'appartenance suit le numéro de mémoire du canal.';

  @override
  String get radioSection => 'Section de la radio';

  @override
  String zoneChannelCount(String name, int count) {
    return '$name ($count canaux)';
  }

  @override
  String get radioSectionsTitle => 'Sections de la radio';

  @override
  String get radioSectionsHelp =>
      'Cette radio comporte des sections de canaux ou sous-appareils distincts. Choisissez une section pour afficher et modifier ses canaux. L\'écriture conserve les autres sections de l\'image enregistrée de la radio. Les banques et zones se modifient séparément.';

  @override
  String get search => 'Rechercher';

  @override
  String get searchHint => 'Rechercher un nom, une fréquence ou une note';

  @override
  String get clearChannelSearch => 'Effacer la recherche de canaux';

  @override
  String bulkEditTip(int count) {
    return 'Modifier ensemble $count canaux sélectionnés';
  }

  @override
  String clearSelectedTip(int count) {
    return 'Vider $count canaux sélectionnés';
  }

  @override
  String get duplicateChannel => 'Dupliquer le canal';

  @override
  String get addChannel => 'Ajouter un canal';

  @override
  String get slots => 'Emplacements';

  @override
  String get showEmptySlotsTip =>
      'Afficher tous les emplacements mémoire, y compris les vides';

  @override
  String get clearColumnFilters => 'Effacer les filtres de colonnes';

  @override
  String editSelected(int count) {
    return 'Modifier $count sélectionnés';
  }

  @override
  String get duplicate => 'Dupliquer';

  @override
  String get showEmptySlots => 'Afficher les emplacements vides';

  @override
  String get clearFilters => 'Effacer les filtres';

  @override
  String get openShort => 'Ouvrir…';

  @override
  String get welcomeTitle => 'Que voulez-vous faire ?';

  @override
  String get welcomeSubtitle =>
      'Ouvrez un fichier CHIRP existant ou lisez les canaux directement depuis votre radio.';

  @override
  String get welcomeLoadTitle => 'Charger une configuration';

  @override
  String get welcomeLoadBody =>
      'Ouvrez un CSV CHIRP ou un fichier image natif et continuez la modification.';

  @override
  String get welcomeLoadHelp =>
      'Ouvrez un CSV compatible CHIRP ou une image radio native. Les images natives conservent le modèle sélectionné et l\'image enregistrée nécessaires au transfert vers la radio.';

  @override
  String get welcomeReadTitle => 'Lire les canaux d\'une radio';

  @override
  String get welcomeReadBody =>
      'Branchez un câble de programmation et importez les canaux actuels de la radio.';

  @override
  String get welcomeConnect => 'Connecter la radio';

  @override
  String get welcomeReadHelp =>
      'Ouvrez l\'écran de connexion de la radio, choisissez votre câble et le modèle exact, puis choisissez Lire les canaux de la radio. Les réglages se lisent séparément, sur la page Réglages de la radio.';

  @override
  String get welcomeRepeatersTitle => 'Trouver des relais à proximité';

  @override
  String get welcomeRepeatersBody =>
      'Cherchez dans RepeaterBook et ajoutez des canaux de relais.';

  @override
  String get welcomeRepeatersHelp =>
      'Cherchez des relais radioamateurs et GMRS dans RepeaterBook, prévisualisez les résultats et ajoutez les canaux sélectionnés à la bibliothèque actuelle.';

  @override
  String get welcomeTip =>
      'Pour écrire dans une radio, il faut d\'abord y lire une image correspondante. Vous pouvez préparer ou modifier un CSV à tout moment, mais l\'écriture dans la radio reste bloquée tant qu\'une lecture n\'est pas terminée.';

  @override
  String get updateCheckFailed => 'Impossible de rechercher les mises à jour';

  @override
  String get updateCheckFailedHint =>
      'Vous pouvez aussi télécharger la dernière version sur newchirp.net.';

  @override
  String get aboutSubtitle =>
      'Informations sur l\'application et licences libres';

  @override
  String get freqRefTitle => 'Référence des fréquences';

  @override
  String get freqRefUsSubtitle =>
      'Plan de canaux FRS/GMRS des États-Unis (Part 95)';

  @override
  String get settingsSubtitle =>
      'Options générales de la radio fournies par le pilote sélectionné';

  @override
  String aboutTagline(String version) {
    return 'Programmateur radio de bureau · Version $version';
  }

  @override
  String get contributor => 'Contributeur';

  @override
  String get chirpLayerTitle => 'Couche de compatibilité CHIRP';

  @override
  String get chirpLayerBody1 =>
      'NewChirp utilise les pilotes de CHIRP pour la compatibilité avec les radios. Les droits d\'auteur de CHIRP appartiennent à ses contributeurs, et CHIRP est un logiciel libre sous licence GNU General Public License, version 3 ou (à votre choix) toute version ultérieure.';

  @override
  String get chirpLayerBody2 =>
      'NewChirp développe aussi ses propres pilotes pour les radios qui n\'ont pas encore de pilote CHIRP ou dont le pilote CHIRP ne fonctionne pas correctement. Ces pilotes maintenus par NewChirp sont publiés sous GPLv3 ou ultérieure et peuvent être intégrés à CHIRP sous la même licence, sous réserve de l\'examen et de l\'acceptation des mainteneurs de CHIRP.';

  @override
  String chirpSource(String url) {
    return 'Projet et code source de CHIRP : $url';
  }

  @override
  String newchirpSource(String url) {
    return 'Projet et code source de NewChirp : $url';
  }

  @override
  String get licensesTitle => 'Licences libres';

  @override
  String get licensesBody =>
      'Le texte complet de la GPL de CHIRP et les licences de pySerial, libusb et des dépendances Flutter sont inclus avec cette application.';

  @override
  String get viewLicenses => 'Voir les licences complètes';

  @override
  String get notAffiliated =>
      'NewChirp est une interface indépendante, ni affiliée ni approuvée par le projet CHIRP.';

  @override
  String get settingsIntro =>
      'Réglez les options générales de la radio, comme le squelch, le rétroéclairage, le VOX et les autres commandes fournies par le pilote CHIRP sélectionné.';

  @override
  String get settingsNoModel =>
      'Aucun modèle de radio sélectionné. Ouvrez d\'abord Connexion de la radio.';

  @override
  String get settingsNoCable => 'Aucun câble de programmation sélectionné';

  @override
  String get settingsReadFromRadio => 'lus depuis la radio';

  @override
  String get settingsSnapshotAvailable => 'copie enregistrée disponible';

  @override
  String get settingsLoading => 'Chargement des réglages de la radio...';

  @override
  String get settingsUnsupportedTitle =>
      'Cette radio ne propose pas de réglages généraux';

  @override
  String get settingsUnsupportedBody =>
      'Le pilote CHIRP sélectionné ne fournit pas de réglages généraux. Les réglages par canal restent disponibles dans l\'éditeur de canaux.';

  @override
  String get settingsLoadError =>
      'Impossible de charger les réglages de la radio';

  @override
  String get settingsReadTitle => 'Lire les réglages de la radio';

  @override
  String get settingsReadBodyConnected =>
      'Lisez les réglages actuels directement depuis la radio connectée. Seuls la copie enregistrée et les réglages sont actualisés ; la liste de canaux actuelle ne change pas.';

  @override
  String get settingsReadBodyDisconnected =>
      'Sélectionnez le câble de programmation et le modèle exact dans Connexion de la radio, puis lisez la radio pour charger ses réglages.';

  @override
  String get openRadioConnection => 'Ouvrir la connexion de la radio';

  @override
  String get settingsNotLoadedTitle =>
      'Les réglages ne sont pas encore chargés';

  @override
  String get settingsNotLoadedConnected =>
      'Lisez les valeurs actuelles depuis la radio connectée, ou utilisez la copie enregistrée de la radio pour les valeurs en mémoire.';

  @override
  String get settingsNotLoadedSnapshot =>
      'Utilisez la copie enregistrée de la radio pour charger les valeurs en mémoire.';

  @override
  String get readSettingsFromRadio => 'Lire les réglages actuels de la radio';

  @override
  String get useSavedSnapshot => 'Utiliser la copie enregistrée de la radio';
}
