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

  @override
  String uiDefaultsComeFromChannelOnlyFields(Object p0) {
    return 'Les valeurs initiales viennent du canal $p0. Seuls les champs modifiés ici s\'appliquent à tous les canaux sélectionnés.';
  }

  @override
  String get uiSelectedChannelsNeedChanges =>
      'Les canaux sélectionnés doivent être corrigés';

  @override
  String get uiBackToEditor => 'Retour à l\'éditeur';

  @override
  String uiUpdatedSelectedChannels(Object p0) {
    return '$p0 canaux sélectionnés mis à jour';
  }

  @override
  String uiConnectTheAndChooseItsPort(Object p0, Object p1) {
    return 'Branchez la $p0 et choisissez son port pour lire $p1.';
  }

  @override
  String get uiBankAndZoneChangesAreReady =>
      'Les modifications des banques et des zones sont prêtes. Écrivez-les avec les canaux.';

  @override
  String get uiCouldnTCompleteThatAction =>
      'Impossible de terminer cette action';

  @override
  String get uiMoreInfo => 'Plus d\'informations :';

  @override
  String get uiSubmitBugReport => 'Envoyer un rapport de bogue';

  @override
  String get uiLoadExperimentalChirpModule =>
      'Charger un module CHIRP expérimental ?';

  @override
  String get uiChirpModulesAreExecutablePythonCode =>
      'Les modules CHIRP sont du code Python exécutable. NewChirp exécute le module dans un environnement isolé qui bloque votre dossier personnel, les autres disques et le réseau. Le module peut tout de même utiliser la radio sélectionnée et les fichiers de cette session.';

  @override
  String get uiOnlyLoadAModuleFromA =>
      'Ne chargez un module que d\'une source de confiance. Un mauvais module peut quand même endommager la radio. Le module reste actif uniquement pendant cette session de NewChirp. Sélectionnez le modèle de radio et relisez la radio avant d\'écrire.';

  @override
  String get uiLoadModule => 'Charger le module';

  @override
  String uiMovedToChannel(Object p0, Object p1) {
    return '$p0 déplacé vers le canal $p1';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations =>
      'Cette radio a des emplacements de canaux fixes : impossible d\'insérer des emplacements vides.';

  @override
  String uiInsertedAnEmptySlotBeforeChannel(Object p0) {
    return 'Emplacement vide inséré avant le canal $p0';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations2 =>
      'Cette radio a des emplacements de canaux fixes : impossible de retirer des emplacements vides.';

  @override
  String uiRemovedEmptySlot(Object p0) {
    return 'Emplacement vide $p0 retiré';
  }

  @override
  String get uiRepeaterbookResults => 'résultats RepeaterBook';

  @override
  String get uiMacosBlockedTheSaveLocation =>
      'macOS a bloqué l\'emplacement d\'enregistrement';

  @override
  String get uiNewchirpDoesNotHavePermissionTo =>
      'NewChirp n\'a pas l\'autorisation d\'écrire dans ce dossier. Choisissez un autre dossier maintenant, ou autorisez l\'accès à NewChirp dans Réglages Système > Confidentialité et sécurité > Fichiers et dossiers.';

  @override
  String get uiChooseAnotherFolder => 'Choisir un autre dossier';

  @override
  String uiStart(Object p0) {
    return 'Commencer $p0 ?';
  }

  @override
  String get uiKeepCurrentList => 'Garder la liste actuelle';

  @override
  String get uiDiscardAndContinue => 'Abandonner et continuer';

  @override
  String uiMarineVhfTemplate(Object p0) {
    return 'Modèle VHF marine : $p0';
  }

  @override
  String get uiStockChannels => 'canaux d\'usine';

  @override
  String get uiDiscardUnsavedSettingsChanges =>
      'Abandonner les modifications de réglages non enregistrées ?';

  @override
  String get uiUsingTheSavedRadioSnapshotWill =>
      'Utiliser la copie enregistrée de la radio remplacera les modifications de réglages non enregistrées de cette page.';

  @override
  String get uiUseSavedSnapshot => 'Utiliser la copie enregistrée';

  @override
  String get uiReplaceUnsavedSettingsChanges =>
      'Remplacer les modifications de réglages non enregistrées ?';

  @override
  String get uiReadingSettingsFromTheRadioWill =>
      'Lire les réglages de la radio remplacera les modifications de réglages non enregistrées de cette page. La liste de canaux actuelle ne change pas.';

  @override
  String get uiReadSettings => 'Lire les réglages';

  @override
  String get uiWhereShouldTheNewChannelGo => 'Où placer le nouveau canal ?';

  @override
  String get uiAtTheEnd => 'À la fin';

  @override
  String get uiBeforeTheSelectedChannel => 'Avant le canal sélectionné';

  @override
  String get uiAfterTheSelectedChannel => 'Après le canal sélectionné';

  @override
  String uiChannelAdded(Object p0) {
    return 'Canal $p0 ajouté';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations3 =>
      'Cette radio a des emplacements de canaux fixes. Les nouveaux canaux ne peuvent être ajoutés qu\'après le dernier canal.';

  @override
  String uiOverwriteChannels(Object p0) {
    return 'Écraser $p0 canaux ?';
  }

  @override
  String uiTheDestinationRangeThroughContainsChannels(
    Object p0,
    Object p1,
    Object p2,
  ) {
    return 'La plage de destination de $p0 à $p1 contient $p2 canaux avec des données. Le collage les remplacera.';
  }

  @override
  String get uiOverwriteChannels2 => 'Écraser les canaux';

  @override
  String uiOverwriteChannel(Object p0) {
    return 'Écraser le canal $p0 ?';
  }

  @override
  String get uiOverwriteChannel2 => 'Écraser le canal';

  @override
  String uiClearedChannelsUseCmdCtrlZ(Object p0) {
    return '$p0 canaux vidés. Utilisez Cmd/Ctrl+Z pour annuler.';
  }

  @override
  String uiStaysInTheRadioTheName(Object p0) {
    return '$p0 reste dans la radio. Le nom est effacé et la fréquence du relais d\'origine est rétablie.';
  }

  @override
  String uiAndMoreChannels(Object p0) {
    return '…et $p0 canaux de plus.';
  }

  @override
  String get uiNamesAreConvertedOnlyWhenThe =>
      'Les noms ne sont convertis que si la radio sélectionnée l\'exige. Les fréquences personnalisées peuvent nécessiter un canal hors de la plage mémoire verrouillée de la radio.';

  @override
  String get uiStopWritingTheRadio => 'Arrêter l\'écriture dans la radio ?';

  @override
  String get uiTheRadioIsBeingWrittenNow =>
      'La radio est en cours d\'écriture. Certaines radios prennent une minute ou deux, et le temps écoulé montre que l\'écriture continue. L\'arrêter en cours de route peut laisser une partie de la mémoire de la radio à moitié écrite ; il faudra peut-être alors l\'éteindre, la rallumer et écrire à nouveau.';

  @override
  String get uiStopAnyway => 'Arrêter quand même';

  @override
  String get uiKeepWriting => 'Continuer l\'écriture';

  @override
  String get uiLater => 'Plus tard';

  @override
  String get uiOpenDownloadPage => 'Ouvrir la page de téléchargement';

  @override
  String get uiDownloadAndInstall => 'Télécharger et installer';

  @override
  String get uiFinishTheCurrentOperationFirst =>
      'Terminez d\'abord l\'opération en cours';

  @override
  String get uiWaitForTheCurrentRadioOr =>
      'Attendez la fin de l\'opération en cours sur la radio ou les fichiers avant d\'installer NewChirp.';

  @override
  String get uiSaveRadioSettingsFirst =>
      'Enregistrez d\'abord les réglages de la radio';

  @override
  String get uiYouHaveRadioSettingChangesThat =>
      'Des modifications des réglages de la radio n\'ont pas été écrites. Enregistrez-les avant d\'installer la mise à jour.';

  @override
  String get uiSaveYourChannelChangesFirst =>
      'Enregistrez d\'abord vos modifications de canaux';

  @override
  String get uiNewchirpWillCloseToInstallThe =>
      'NewChirp va se fermer pour installer la mise à jour. Enregistrez la liste de canaux actuelle avant de continuer.';

  @override
  String get uiSaveAndContinue => 'Enregistrer et continuer';

  @override
  String get uiInstallingNewchirpUpdate =>
      'Installation de la mise à jour de NewChirp';

  @override
  String get uiNewchirpWillCloseAndReopenAutomatically =>
      'NewChirp se fermera et se rouvrira automatiquement quand le programme d\'installation sera prêt.';

  @override
  String get uiUpdateCouldNotBeInstalled =>
      'Impossible d\'installer la mise à jour';

  @override
  String uiYouCanStillDownloadTheLatest(Object p0) {
    return '$p0\n\nVous pouvez toujours télécharger la dernière version sur newchirp.net.';
  }

  @override
  String get uiCouldnTOpenYourBrowser =>
      'Impossible d\'ouvrir votre navigateur';

  @override
  String uiNewchirpCouldNotStartTheBrowser(Object p0) {
    return 'NewChirp n\'a pas pu lancer le navigateur sur cet ordinateur. Ouvrez vous-même cette adresse pour obtenir la mise à jour :\n\n$p0';
  }

  @override
  String get uiCopyLink => 'Copier le lien';

  @override
  String get uiYouReUpToDate => 'Vous êtes à jour';

  @override
  String uiNewchirpIsTheLatestVersion(Object p0) {
    return 'NewChirp $p0 est la dernière version.';
  }

  @override
  String uiChannelIsOccupied(Object p0) {
    return 'Le canal $p0 est occupé';
  }

  @override
  String get uiReplace => 'Remplacer';

  @override
  String get uiSwap => 'Échanger';

  @override
  String get uiMoveAndShift => 'Déplacer et décaler';

  @override
  String uiChannelsScanEnabledNeedAttention(Object p0, Object p1, Object p2) {
    return '$p0 canaux · $p1 en balayage · $p2 à vérifier';
  }

  @override
  String get uiReview => 'Vérifier';

  @override
  String get uiNoRadioImageLoadedEditingAnd =>
      'Aucune image de radio chargée. La modification et l\'export CSV fonctionnent, mais l\'écriture reste bloquée tant que vous n\'avez pas lu cette radio.';

  @override
  String get uiChannelEditing => 'Modification des canaux';

  @override
  String get uiAddLetsYouPlaceANew =>
      'Ajouter permet de placer un nouveau canal à la fin, avant le canal sélectionné ou après. Avant et Après décalent les canaux suivants dans les emplacements mémoire de la radio. Dupliquer copie la ligne sélectionnée, et Supprimer la retire après confirmation. Double-cliquez sur une ligne pour modifier tous ses champs. Faites un clic droit sur une ligne pour la copier, la couper, la coller, la dupliquer ou la vider. Copier ou couper une sélection de plusieurs lignes copie les canaux actifs en bloc ; le collage place le bloc à la ligne cible. Un clic sélectionne une ligne. Maj+clic sélectionne une plage, et Cmd/Ctrl+clic ajoute ou retire des lignes. Utilisez la modification groupée pour changer les propriétés de toutes les lignes sélectionnées ; seuls les champs modifiés sont appliqués. Faites un clic droit et choisissez Propriétés pour ouvrir le même éditeur. Faites glisser la poignée au bord gauche d\'une ligne pour la déplacer ; les canaux intermédiaires se décalent dans les mêmes emplacements mémoire. Afficher les emplacements vides garde visible la disposition de la mémoire de la radio ; double-cliquez sur un emplacement vide pour y créer un canal. Vider retire de la radio la ligne sélectionnée, ou toutes les lignes sélectionnées, à la prochaine écriture. Utilisez Cmd/Ctrl+Z pour annuler et Cmd/Ctrl+Maj+Z pour rétablir.';

  @override
  String get uiChooseAPrinter => 'Choisissez une imprimante';

  @override
  String get uiPrintJobSent => 'Impression envoyée';

  @override
  String uiWasSentTo(Object p0, Object p1) {
    return '$p0 a été envoyé à $p1.';
  }

  @override
  String get uiUsFrsGmrs => 'FRS / GMRS (États-Unis)';

  @override
  String uiReferenceSourceVerifyCurrentNationalRules(Object p0) {
    return 'Source de référence : $p0 Vérifiez la réglementation nationale en vigueur avant d\'émettre.';
  }

  @override
  String get uiGmrsFrsFrequencyReference =>
      'Référence des fréquences GMRS et FRS';

  @override
  String get uiUnitedStatesPartChannelPlanColor =>
      'Plan de canaux Part 95 des États-Unis, avec couleurs par bande de fréquences et classe de puissance.';

  @override
  String get uiRepeaterPairsGmrsOnly => 'Paires de relais (GMRS uniquement)';

  @override
  String get uiKeyNotes => 'Points importants';

  @override
  String get uiAllFrequenciesAreInMhzGmrs =>
      'Toutes les fréquences sont en MHz. Le GMRS exige une licence de la FCC ; le FRS est utilisable sans licence individuelle.\nLes radios GMRS mobiles ou fixes ne peuvent pas émettre sur les canaux 8-14. Les entrées de relais sont réservées au GMRS.\nPar usage, le canal 20 (462,675 MHz) avec CTCSS 141,3 Hz sert souvent de canal de voyage et d\'assistance.\nÀ titre de référence uniquement : vérifiez la réglementation FCC Part 95 en vigueur et le manuel de votre radio.';

  @override
  String get uiNoEditableOptionsInThisGroup =>
      'Aucune option modifiable dans ce groupe.';

  @override
  String get uiKeepTheRadioPoweredOnAnd =>
      'Gardez la radio allumée et le câble branché.';

  @override
  String uiThisSettingTypeIsNotSupported(Object p0) {
    return '$p0 : ce type de réglage n\'est pas encore pris en charge.';
  }

  @override
  String get uiSearchAbbreviationsOrDefinitions =>
      'Rechercher des abréviations ou des définitions';

  @override
  String get uiNoMatchingTerms => 'Aucun terme correspondant.';

  @override
  String get uiThanksTheDiagnosticLogAndError =>
      'Merci. Le journal de diagnostic et les détails de l\'erreur ont été envoyés au développeur de NewChirp.';

  @override
  String get uiYourEmail => 'Votre adresse e-mail';

  @override
  String get uiUsedOnlyIfTheDeveloperNeeds =>
      'Utilisée uniquement si le développeur a besoin de plus d\'informations.';

  @override
  String get uiWhatWereYouTryingToDo => 'Qu\'essayiez-vous de faire ?';

  @override
  String get uiTheReportIncludesAppAndOperating =>
      'Le rapport inclut les versions de l\'application et du système d\'exploitation, la radio et le port série sélectionnés, et les événements de diagnostic récents. Le contenu des canaux et les fichiers chargés ne sont pas enregistrés.';

  @override
  String uiPreviewDiagnosticEvents(Object p0) {
    return 'Aperçu de $p0 événements de diagnostic';
  }

  @override
  String uiFilterCounties(Object p0) {
    return 'Filtrer les comtés de $p0';
  }

  @override
  String get uiFindACounty => 'Trouver un comté';

  @override
  String uiOfCounties(Object p0, Object p1) {
    return '$p0 comtés sur $p1';
  }

  @override
  String get uiClearAll => 'Tout effacer';

  @override
  String get uiNoMatchingCounties => 'Aucun comté correspondant.';

  @override
  String get uiNoCoordinatesAreAvailableForThese =>
      'Aucune coordonnée disponible pour ces résultats.';

  @override
  String uiMappedTapAPinToSelect(Object p0) {
    return '$p0 sur la carte • touchez un repère pour le sélectionner';
  }

  @override
  String get uiSearchARepeaterDirectoryAndAdd =>
      'Cherchez dans un annuaire de relais et ajoutez les canaux sélectionnés à votre bibliothèque actuelle. Vérifiez l\'état et l\'accès du relais avant d\'émettre.';

  @override
  String get uiDirectory => 'Annuaire';

  @override
  String get uiMygmrsRequiresAnActiveGmrsLicense =>
      'myGMRS exige une licence GMRS active pour les fréquences des relais. Les tonalités PL et les règles nécessitent un abonnement Premium. Cette connexion dure jusqu\'à la fermeture de NewChirp.';

  @override
  String get uiCountry => 'Pays';

  @override
  String get uiSortResults => 'Trier les résultats';

  @override
  String get uiSourceOrder => 'Ordre de la source';

  @override
  String get uiFrequency => 'Fréquence';

  @override
  String get uiCallsignName => 'Indicatif / nom';

  @override
  String get uiCity => 'Ville';

  @override
  String get uiCounty => 'Comté';

  @override
  String get uiService => 'Service';

  @override
  String get uiAmateurGmrs => 'Radioamateur + GMRS';

  @override
  String get uiAmateurHam => 'Radioamateur';

  @override
  String get uiClearRepeaterSearch => 'Effacer la recherche de relais';

  @override
  String get uiLatitudeOptional => 'Latitude (facultatif)';

  @override
  String get uiLongitudeOptional => 'Longitude (facultatif)';

  @override
  String get uiRadiusKm => 'Rayon en km';

  @override
  String get uiOpenRepeatersOnly => 'Relais ouverts uniquement';

  @override
  String get uiFmCapableOnly => 'Compatibles FM uniquement';

  @override
  String get uiSearchAmateurRepeatersInstead =>
      'Chercher plutôt des relais radioamateurs';

  @override
  String get uiFilterLoadedResults => 'Filtrer les résultats chargés';

  @override
  String get uiCityCountyCallsignModeServiceOr =>
      'Ville, comté, indicatif, mode, service ou fréquence';

  @override
  String get uiClearResultFilter => 'Effacer le filtre des résultats';

  @override
  String get uiList => 'Liste';

  @override
  String get uiMap => 'Carte';

  @override
  String get uiSelectAll => 'Tout sélectionner';

  @override
  String get uiClear => 'Effacer';

  @override
  String get uiDataCourtesyOfRepeaterbookCom =>
      'Données fournies par RepeaterBook.com.';

  @override
  String get uiDragToResize => 'Faites glisser pour redimensionner';

  @override
  String get uiInsertEmptySlotBefore => 'Insérer un emplacement vide avant';

  @override
  String get uiRemoveEmptySlot => 'Retirer l\'emplacement vide';

  @override
  String uiMove(Object p0) {
    return 'Déplacer $p0';
  }

  @override
  String get uiDragRowsToRearrangeChannels =>
      'Faites glisser les lignes pour réorganiser les canaux';

  @override
  String get uiFilter => 'Filtrer';

  @override
  String get uiNoMatchingChannels => 'Aucun canal correspondant';

  @override
  String get uiWriteChannelsToRadio => 'Écrire les canaux dans la radio';

  @override
  String get uiThanksTheDiagnosticLogAndProblem =>
      'Merci. Le journal de diagnostic et les détails du problème ont été envoyés au développeur de NewChirp.';

  @override
  String get uiTheReportIncludesAppAndOperating2 =>
      'Le rapport inclut les versions de l\'application et du système d\'exploitation, la radio sélectionnée, le firmware s\'il est disponible, le port série et les événements de diagnostic récents. Le contenu des canaux et les fichiers chargés ne sont pas enregistrés.';

  @override
  String get uiSaveFile => 'Enregistrer le fichier';

  @override
  String get uiDoNotShowMeThisMessage => 'Ne plus afficher ce message';

  @override
  String get uiMarineVhfChannelTemplate => 'Modèle de canaux VHF marine';

  @override
  String get uiPlan => 'Plan';

  @override
  String uiSource(Object p0) {
    return 'Source : $p0';
  }

  @override
  String get uiTheChannelPlanIsSelectedBy =>
      'Le plan de canaux se choisit par région réglementaire, pas par code postal. Les attributions de canaux marins sont nationales ou internationales et ne changent pas selon le code postal.';

  @override
  String get uiProgramShipTransmitFrequencies =>
      'Programmer les fréquences d\'émission navire';

  @override
  String get uiReceiveOnlyIsTheSafeDefault =>
      'La réception seule est le choix sûr par défaut. Activez cette option uniquement si la radio et l\'installation sont autorisées à émettre en VHF marine.';

  @override
  String get uiMostAmateurTransceiversAreNotType =>
      'La plupart des émetteurs-récepteurs radioamateurs ne sont pas homologués pour émettre dans la bande marine. Les canaux interdits et en réception seule restent sans émission.';

  @override
  String uiChannelsTransmitCapableReceiveOnly(Object p0, Object p1, Object p2) {
    return '$p0 canaux : $p1 avec émission, $p2 en réception seule.';
  }

  @override
  String get uiAllRowsWillBeAddedReceive =>
      'Toutes les lignes seront ajoutées en réception seule (Duplex \"off\"). La radio bipera et n\'émettra pas sur ces canaux. Cochez la case ci-dessus pour programmer les fréquences d\'émission.';

  @override
  String get uiContinue => 'Continuer';

  @override
  String get uiType => 'Type';

  @override
  String get uiThisRadioDoesNotExposeEditable =>
      'Cette radio ne propose pas de banques modifiables.';

  @override
  String get uiTheseBanksAreFixedByThe =>
      'Ces banques sont fixées par la radio et affichées pour référence.';

  @override
  String get uiUseTheseChanges => 'Utiliser ces modifications';

  @override
  String get uiFindAChannel => 'Trouver un canal';

  @override
  String uiChannel(Object p0) {
    return 'Canal $p0';
  }

  @override
  String get uiLoadingRadioCatalog => 'Chargement du catalogue des radios…';

  @override
  String get uiActionFailed => 'L\'action a échoué';

  @override
  String uiMacosBlockedNewchirpFromWritingTo(Object p0) {
    return '$p0\n\nmacOS a empêché NewChirp d\'écrire dans ce dossier. Choisissez un autre emplacement d\'enregistrement, ou autorisez l\'accès à NewChirp dans :\n\nRéglages Système > Confidentialité et sécurité > Fichiers et dossiers > NewChirp\n\nAccordez l\'accès à Documents, puis réessayez d\'enregistrer.';
  }

  @override
  String uiOnLinuxThisUsuallyMeansYour(Object p0) {
    return '$p0\n\nSous Linux, cela signifie généralement que votre utilisateur n\'a pas l\'autorisation d\'ouvrir le câble de programmation de la radio.\n\nPour corriger :\n    sudo usermod -aG dialout \$USER\n\nPuis déconnectez-vous et reconnectez-vous, rebranchez le câble et réessayez.\n\nPour la session de terminal actuelle uniquement :\n    newgrp dialout';
  }

  @override
  String get uiMototrboCpsChannels => 'canaux MOTOTRBO CPS 2.0';

  @override
  String get uiCsvChannels => 'canaux CSV';

  @override
  String get uiRefreshingRadioCatalog =>
      'Actualisation du catalogue des radios…';

  @override
  String get uiThisChirpImage => 'cette image CHIRP';

  @override
  String get uiNoEmptyChannelSlotIsAvailable =>
      'Aucun emplacement de canal vide n\'est disponible.';

  @override
  String get uiNoEmptyChannelSlotsAreAvailable =>
      'Aucun emplacement de canal vide n\'est disponible sur cette radio.';

  @override
  String get uiSavingChannelLibrary =>
      'Enregistrement de la bibliothèque de canaux…';

  @override
  String get uiSaveCanceled => 'Enregistrement annulé';

  @override
  String get uiDiscardTheCurrentChannelListAny =>
      'Abandonner la liste de canaux actuelle ? Les modifications non enregistrées seront perdues.';

  @override
  String uiCloseTheCurrentChannelListAnd(Object p0) {
    return 'Fermer la liste de canaux actuelle et commencer $p0 ?';
  }

  @override
  String get uiANewBlankConfiguration => 'une nouvelle configuration vierge';

  @override
  String get uiReadingRadioSettingsDoNotDisconnect =>
      'Lecture des réglages de la radio : ne la déconnectez pas...';

  @override
  String get uiSelectAChannelFirst => 'Sélectionnez d\'abord un canal';

  @override
  String get uiThisRadioHasFixedChannelLocations4 =>
      'Cette radio a des emplacements de canaux fixes.';

  @override
  String uiAndFollowingChannelsMoveDownOne(Object p0) {
    return '$p0 et les canaux suivants descendent d\'un emplacement.';
  }

  @override
  String uiUseChannelAfterTheFinalChannel(Object p0) {
    return 'Utiliser le canal $p0, après le dernier canal.';
  }

  @override
  String get uiTheCopiedChannelDoesNotFit =>
      'Le canal copié ne tient pas dans la mémoire de cette radio.';

  @override
  String get uiTheCopiedChannelsDoNotFit =>
      'Les canaux copiés ne tiennent pas à partir de cette ligne.';

  @override
  String get uiThisChannelContainsDataPastingWill =>
      'Ce canal contient des données. Le collage les remplacera.';

  @override
  String uiContainsDataPastingWillReplaceIt(Object p0) {
    return '« $p0 » contient des données. Le collage les remplacera.';
  }

  @override
  String get uiLoadingRadioInstructions =>
      'Chargement des instructions de la radio…';

  @override
  String get uiRestoringChannelsFromTheStoredRadio =>
      'Restauration des canaux depuis l\'image enregistrée de la radio…';

  @override
  String get uiSomeChannelsWereNotWritten =>
      'Certains canaux n\'ont pas été écrits';

  @override
  String get uiSomeChannelValuesWereAdjusted =>
      'Certaines valeurs de canaux ont été ajustées';

  @override
  String uiTheWriteFinishedChannelsWereAdjusted(Object p0, Object p1) {
    return 'L\'écriture est terminée. $p0 canaux ont été ajustés et $p1 n\'ont pas pu être écrits.';
  }

  @override
  String uiTheCompatibleChannelsWereWrittenBut(Object p0) {
    return 'Les canaux compatibles ont été écrits, mais $p0 canaux n\'ont pas pu l\'être.';
  }

  @override
  String get uiTheWriteFinishedButNewchirpAdjusted =>
      'L\'écriture est terminée, mais NewChirp a ajusté des valeurs que la radio n\'accepte pas.';

  @override
  String uiChannelCouldNotBeWritten(Object p0, Object p1, Object p2) {
    return 'Le canal $p0 $p1 n\'a pas pu être écrit : $p2';
  }

  @override
  String uiNameChangedFromTo(Object p0, Object p1) {
    return 'nom changé de \"$p0\" en \"$p1\"';
  }

  @override
  String uiLockedFieldSEverythingElseWas(Object p0) {
    return 'champs verrouillés : $p0 ; tout le reste a été écrit';
  }

  @override
  String get uiCancellingSafely => 'Annulation en toute sécurité…';

  @override
  String get uiUpdateAvailable => 'Mise à jour disponible';

  @override
  String uiNewchirpIsReady(Object p0) {
    return 'NewChirp $p0 est prêt';
  }

  @override
  String uiNewchirpIsAvailableYouAreRunning(Object p0, Object p1) {
    return 'NewChirp $p0 est disponible. Vous utilisez la $p1.\n\nOuvrez la page de téléchargement pour obtenir le programme d\'installation adapté à votre ordinateur.';
  }

  @override
  String uiYouAreRunningNewchirpCanDownload(Object p0, Object p1) {
    return 'Vous utilisez la $p0. NewChirp peut télécharger et installer la $p1 pour vous, puis se rouvrir automatiquement. Inutile d\'aller sur le site web.';
  }

  @override
  String get uiPreparingTheUpdateDownload =>
      'Préparation du téléchargement de la mise à jour…';

  @override
  String uiDownloadingNewchirp(Object p0) {
    return 'Téléchargement de NewChirp $p0…';
  }

  @override
  String get uiVerifiedStartingTheInstallerAndRestarting =>
      'Vérifié. Lancement du programme d\'installation et redémarrage de NewChirp…';

  @override
  String get uiNewchirpCouldNotPrepareTheUpdate =>
      'NewChirp n\'a pas pu préparer la mise à jour.';

  @override
  String uiDeleteChannel(Object p0) {
    return 'Supprimer le canal $p0 ?';
  }

  @override
  String get uiRepeaterRowsThroughStayInThe =>
      'Les lignes de relais 15 à 22 restent dans la radio. Le nom est effacé et la fréquence du relais GMRS d\'origine est rétablie.';

  @override
  String get uiThisChannelWillBeRemovedFrom =>
      'Ce canal sera retiré de la configuration actuelle.';

  @override
  String uiWillBeRemovedFromTheCurrent(Object p0) {
    return '« $p0 » sera retiré de la configuration actuelle.';
  }

  @override
  String uiStoredImageReadyForYouCan(Object p0) {
    return 'Image enregistrée prête pour $p0. Vous pouvez écrire sans relire la radio.';
  }

  @override
  String get uiARadioImageIsLoadedFrom =>
      'Une image de la radio est chargée pour cette session. Vérifiez toutes les modifications avant d\'écrire.';

  @override
  String get uiClearSearchAndColumnFiltersTo =>
      'Effacez la recherche et les filtres de colonnes pour réorganiser les canaux';

  @override
  String get uiRearrangeChannels => 'Réorganiser les canaux';

  @override
  String get uiPreparingFrequencyReference =>
      'Préparation de la référence des fréquences…';

  @override
  String get uiPrintingFrequencyReference =>
      'Impression de la référence des fréquences…';

  @override
  String get uiTheGmrsFrsReference => 'La référence GMRS/FRS';

  @override
  String get uiNewchirpChannelList => 'Liste des canaux NewChirp';

  @override
  String uiNewchirpChannelList2(Object p0) {
    return 'Liste des canaux NewChirp : $p0';
  }

  @override
  String get uiPreparingChannelList => 'Préparation de la liste des canaux…';

  @override
  String get uiChannelList => 'la liste des canaux';

  @override
  String get uiPrintingChannelList => 'Impression de la liste des canaux…';

  @override
  String get uiTheChannelList => 'La liste des canaux';

  @override
  String get uiNoPrintersFound => 'Aucune imprimante trouvée';

  @override
  String uiNewchirpCouldNotFindAnySystem(Object p0) {
    return 'NewChirp n\'a trouvé aucune imprimante système : le PDF de $p0 a donc été ouvert dans votre lecteur PDF par défaut. Utilisez la commande Imprimer du lecteur pour l\'imprimer.';
  }

  @override
  String uiThePdfWasOpenedInYour(Object p0) {
    return 'Le PDF de $p0 a été ouvert dans votre lecteur PDF par défaut. Utilisez la commande Imprimer du lecteur pour l\'imprimer.';
  }

  @override
  String get uiFrequencyMhz => 'Fréquence (MHz)';

  @override
  String get uiUseNotes => 'Usage / notes';

  @override
  String get uiSharedMhzInterstitial => 'Intercalaire 462 MHz partagé';

  @override
  String get uiHandheldOnly => 'Portatifs uniquement';

  @override
  String get uiMainRepeaterOutput => 'Principal / sortie de relais';

  @override
  String get uiChMhzInterstitial => 'Can. 1-7 : intercalaires 462 MHz';

  @override
  String get uiChMhzInterstitial2 => 'Can. 8-14 : intercalaires 467 MHz';

  @override
  String get uiChMhzMain => 'Can. 15-22 : principaux 462 MHz';

  @override
  String get uiFrsPower => 'Puissance FRS';

  @override
  String get uiGmrsPower => 'Puissance GMRS';

  @override
  String get uiInputYouTransmit => 'Entrée - vous émettez';

  @override
  String get uiOutputYouListen => 'Sortie - vous écoutez';

  @override
  String get uiInputOutputMhz => 'Entrée = sortie + 5 MHz';

  @override
  String get uiPreparingTransfer => 'Préparation du transfert...';

  @override
  String get uiWaitingForTheRadioToReport =>
      'En attente de la progression de la radio';

  @override
  String uiCompleteElapsed(Object p0, Object p1) {
    return '$p0 % terminé  |  $p1 écoulé';
  }

  @override
  String get uiEnterAWholeNumber => 'Saisissez un nombre entier';

  @override
  String uiValueMustBeAtLeast(Object p0) {
    return 'La valeur doit être d\'au moins $p0';
  }

  @override
  String uiValueMustBeAtMost(Object p0) {
    return 'La valeur doit être d\'au plus $p0';
  }

  @override
  String uiUseAtLeastCharacters(Object p0) {
    return 'Utilisez au moins $p0 caractères';
  }

  @override
  String uiUseAtMostCharacters(Object p0) {
    return 'Utilisez au plus $p0 caractères';
  }

  @override
  String get uiEnterAValidEmailAddress =>
      'Saisissez une adresse e-mail valide.';

  @override
  String get uiCouldNotSendTheErrorReport =>
      'Impossible d\'envoyer le rapport d\'erreur.';

  @override
  String get uiErrorReportSent => 'Rapport d\'erreur envoyé';

  @override
  String get uiSubmitErrorReport => 'Envoyer un rapport d\'erreur';

  @override
  String get uiNoDiagnosticEventsRecorded =>
      'Aucun événement de diagnostic enregistré.';

  @override
  String get uiSendReport => 'Envoyer le rapport';

  @override
  String get uiWaitingForMygmrsSignInYou =>
      'En attente de la connexion à myGMRS. Vous pouvez annuler cette tentative.';

  @override
  String get uiSignedInToMygmrsForThis =>
      'Connecté à myGMRS pour cette session.';

  @override
  String get uiMygmrsSignInCancelled => 'Connexion à myGMRS annulée.';

  @override
  String get uiSigningOutOfMygmrs => 'Déconnexion de myGMRS…';

  @override
  String get uiSignedOutOfMygmrs => 'Déconnecté de myGMRS.';

  @override
  String get uiEnterBothLatitudeAndLongitudeOr =>
      'Saisissez la latitude et la longitude, ou aucune des deux.';

  @override
  String get uiLatitudeMustBeBetweenAnd =>
      'La latitude doit être comprise entre -90 et 90.';

  @override
  String get uiLongitudeMustBeBetweenAnd =>
      'La longitude doit être comprise entre -180 et 180.';

  @override
  String get uiUseEitherAZipCodeOr =>
      'Utilisez un code postal ou des coordonnées, pas les deux.';

  @override
  String get uiLatitudeAndLongitudeAreRequiredFor =>
      'La latitude et la longitude sont nécessaires pour une recherche par rayon.';

  @override
  String get uiRadiusMustBeGreaterThanZero =>
      'Le rayon doit être supérieur à zéro.';

  @override
  String get uiSignInToMygmrsBeforeSearching =>
      'Connectez-vous à myGMRS avant de chercher.';

  @override
  String get uiSigningInToMygmrs => 'Connexion à myGMRS…';

  @override
  String get uiSearchingRepeaterbook => 'Recherche dans RepeaterBook…';

  @override
  String get uiMygmrsRequiresAnActiveGmrsLicense2 =>
      'myGMRS exige une licence GMRS active pour afficher les fréquences des relais. Vérifiez que vous êtes connecté avec un compte admissible. La recherche texte de myGMRS ne reconnaît pas les noms de comtés ; saisissez un code postal à 5 chiffres pour chercher des relais à proximité.';

  @override
  String get uiRepeaterbookMayNotHaveAGmrs =>
      'RepeaterBook n\'a peut-être pas encore de relais GMRS pour cette zone.';

  @override
  String get uiCoordinatesAreSearchedWithinTheSelected =>
      'Les coordonnées sont recherchées dans la région sélectionnée.';

  @override
  String get uiCheckThatCountryAndRegionAre =>
      'Vérifiez que le pays et la région sont corrects.';

  @override
  String uiNoMatchingGmrsRepeatersWereFound(Object p0, Object p1, Object p2) {
    return 'Aucun relais GMRS correspondant trouvé$p0. $p1 $p2';
  }

  @override
  String get uiOpenUse => 'usage ouvert';

  @override
  String get uiFmAnalog => 'FM analogique';

  @override
  String uiNoMatchingRepeatersWereFoundZip(Object p0, Object p1) {
    return 'Aucun relais correspondant trouvé$p0. Les recherches par code postal utilisent 50 km par défaut ; augmentez le rayon ou désactivez les filtres actifs.$p1';
  }

  @override
  String uiNoMatchingRepeatersWereFoundCoordinates(Object p0, Object p1) {
    return 'Aucun relais correspondant trouvé$p0. Les coordonnées sont recherchées dans la région sélectionnée. Augmentez le rayon ou désactivez les filtres actifs.$p1';
  }

  @override
  String uiNoMatchingRepeatersWereFoundCheck(Object p0, Object p1) {
    return 'Aucun relais correspondant trouvé$p0. Vérifiez la région sélectionnée ou augmentez le rayon.$p1';
  }

  @override
  String get uiNoTone => 'sans tonalité';

  @override
  String get uiCancelSignIn => 'Annuler la connexion';

  @override
  String get uiSignOut => 'Se déconnecter';

  @override
  String get uiSignInToMygmrs => 'Se connecter à myGMRS';

  @override
  String get uiRepeaterNameCityOrZipCode =>
      'Nom du relais, ville ou code postal';

  @override
  String get uiCityZipCountyCallsignLandmarkOr =>
      'Ville, code postal, comté, indicatif, lieu ou notes';

  @override
  String get uiADigitZipSearchesNearbyRepeaters =>
      'Un code postal à 5 chiffres cherche les relais à proximité. myGMRS ne prend pas en charge les noms de comtés.';

  @override
  String get uiADigitZipSearchesRepeatersWithin =>
      'Un code postal à 5 chiffres cherche les relais à moins de 50 km par défaut.';

  @override
  String get uiAllCounties => 'Tous les comtés';

  @override
  String get uiSearchToPreviewRepeaterChannels =>
      'Lancez une recherche pour prévisualiser les canaux des relais.';

  @override
  String uiShownOfLoadedDataFrom(Object p0, Object p1, Object p2) {
    return '$p0 affichés sur $p1 chargés • Données de $p2';
  }

  @override
  String get uiAddSelected => 'Ajouter la sélection';

  @override
  String uiAddSelected2(Object p0) {
    return 'Ajouter $p0 sélectionnés';
  }

  @override
  String get uiEditSelectedProperties =>
      'Modifier les propriétés sélectionnées';

  @override
  String uiCopyChannels(Object p0) {
    return 'Copier $p0 canaux';
  }

  @override
  String uiCutChannels(Object p0) {
    return 'Couper $p0 canaux';
  }

  @override
  String uiPasteChannels(Object p0) {
    return 'Coller $p0 canaux';
  }

  @override
  String uiClearSelectedChannels(Object p0) {
    return 'Vider $p0 canaux sélectionnés';
  }

  @override
  String get uiClearChannel => 'Vider le canal';

  @override
  String get uiEmptyMemorySlotDoubleClickTo =>
      'Emplacement mémoire vide. Double-cliquez pour créer un canal.';

  @override
  String get uiDoubleClickToEditChannel =>
      'Double-cliquez pour modifier le canal';

  @override
  String get uiDragToRearrangeChannel =>
      'Faites glisser pour déplacer le canal';

  @override
  String get uiEmptySlot => 'Emplacement vide';

  @override
  String get uiBugReportSent => 'Rapport de bogue envoyé';

  @override
  String get uiSubmitBugReport2 => 'Envoyer un rapport de bogue';

  @override
  String uiGiveEveryEntryANameBefore(Object p0) {
    return 'Donnez un nom à chaque entrée $p0 avant d\'enregistrer.';
  }

  @override
  String get uiAddAChannelToCreate => 'Ajoutez un canal pour la créer';

  @override
  String get uiAChannelMayBelongToMore =>
      'Un canal peut appartenir à plusieurs entrées.';

  @override
  String get uiAChannelCanBelongToOne =>
      'Un canal ne peut appartenir qu\'à une seule entrée.';

  @override
  String get uiThisEmptyEntryIsTheRadio =>
      'Cette entrée vide est la banque ou zone libre de la radio. Ajoutez un canal pour la créer.';

  @override
  String uiChannelsSelected(Object p0) {
    return '$p0 canaux sélectionnés';
  }

  @override
  String get glossFrs =>
      'Family Radio Service. Service UHF des États-Unis sans licence.';

  @override
  String get glossGmrs =>
      'General Mobile Radio Service. Service UHF des États-Unis soumis à licence.';

  @override
  String get glossRx =>
      'Réception. La fréquence ou la tonalité utilisée à l\'écoute.';

  @override
  String get glossTx =>
      'Émission. La fréquence ou la tonalité utilisée pour émettre.';

  @override
  String get glossCtcss =>
      'Continuous Tone-Coded Squelch System. Une tonalité analogique subaudible, souvent appelée tonalité PL.';

  @override
  String get glossTsql =>
      'Squelch par tonalité. Exige la même tonalité CTCSS en réception et en émission.';

  @override
  String get glossDcs =>
      'Digital-Coded Squelch System. Un code de squelch numérique ; NewChirp l\'appelle DTCS.';

  @override
  String get glossDtcs =>
      'Digital-Coded Squelch System. Un code numérique utilisé comme une tonalité CTCSS pour ouvrir un récepteur ou un relais.';

  @override
  String get glossDtcsPol =>
      'Polarité DTCS. La polarité normale ou inversée doit être la même sur la radio et le relais.';

  @override
  String get glossFm =>
      'Modulation de fréquence. Mode vocal analogique standard.';

  @override
  String get glossNfm =>
      'FM bande étroite. Occupe moins de bande passante ; courante en FRS, GMRS et sur les réseaux de relais chargés.';

  @override
  String get glossAm =>
      'Modulation d\'amplitude. Utilisée par certains canaux aéronautiques et radioamateurs.';

  @override
  String get glossDuplex =>
      'Relation émission/réception. Simplex utilise la même fréquence ; les décalages et le mode split utilisent une autre fréquence d\'émission.';

  @override
  String get glossOffset =>
      'L\'écart de fréquence entre réception et émission.';

  @override
  String get glossSplit =>
      'Fréquences de réception et d\'émission indépendantes, au lieu d\'un décalage fixe.';

  @override
  String get glossStep => 'Pas d\'accord utilisé pour changer de fréquence.';

  @override
  String get glossScan =>
      'Indique si le canal est inclus dans le balayage ou marqué pour être ignoré.';

  @override
  String get glossBcl =>
      'Busy Channel Lockout. Empêche d\'émettre quand le canal est déjà occupé.';

  @override
  String get glossPttId =>
      'Identification de la station envoyée au début ou à la fin d\'une émission, selon la radio.';

  @override
  String get glossSCode =>
      'Sélecteur de code de signalisation. Choisit le code PTT-ID ou de signalisation enregistré utilisé par le canal.';

  @override
  String get fileSaveWarning =>
      'Enregistrer ce fichier n\'écrit pas ces modifications dans votre radio. Vous devez écrire les modifications dans la radio pour qu\'elles prennent effet.';

  @override
  String repeaterRangeIn(String location) {
    return ' en $location';
  }

  @override
  String repeaterRangeZip(String km, String zip, String location) {
    return ' à moins de $km km du code postal $zip en $location';
  }

  @override
  String repeaterRangeCoords(String km, String location) {
    return ' à moins de $km km de vos coordonnées en $location';
  }

  @override
  String repeaterFilterHint(String filters) {
    return ' Les filtres actifs exigent $filters ; essayez de les désactiver.';
  }

  @override
  String get listAnd => ' et ';

  @override
  String occupiedBody(String occupant, Object channel, String moving) {
    return '$occupant utilise déjà le canal $channel. Choisissez comment placer $moving.';
  }

  @override
  String get anExistingChannel => 'Un canal existant';

  @override
  String get thisChannel => 'ce canal';

  @override
  String channelsNeedAttention(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count canaux sont à vérifier avant l\'écriture.',
      one: '1 canal est à vérifier avant l\'écriture.',
    );
    return '$_temp0';
  }

  @override
  String moreValidationIssues(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count autres problèmes de validation.',
      one: '1 autre problème de validation.',
    );
    return '$_temp0';
  }

  @override
  String repeatersNoneImportable(int count, String source) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other:
          '$source a renvoyé $count relais correspondants, mais aucun n\'a pu être importé.',
      one:
          '$source a renvoyé 1 relais correspondant, mais aucun n\'a pu être importé.',
    );
    return '$_temp0';
  }

  @override
  String countyCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count comtés',
      one: '1 comté',
    );
    return '$_temp0';
  }
}
