// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get navRadioConnection => 'Conexión de la radio';

  @override
  String get navChannelLibrary => 'Biblioteca de canales';

  @override
  String get navRadioSettings => 'Ajustes de la radio';

  @override
  String get navFindRepeaters => 'Buscar repetidores';

  @override
  String get navFrequencyReference => 'Referencia de frecuencias';

  @override
  String get navAbout => 'Acerca de y licencias';

  @override
  String get sidebarDesktopProgrammer => 'PROGRAMADOR DE RADIOS DE ESCRITORIO';

  @override
  String get sidebarLeadProgrammer => 'Programador principal';

  @override
  String sidebarVersion(String version) {
    return 'Versión $version';
  }

  @override
  String get languageLabel => 'Idioma';

  @override
  String get languageSystem => 'Idioma del sistema';

  @override
  String get languageBetaNote =>
      'Las traducciones están en beta. Los mensajes de los controladores de radio siguen en inglés.';

  @override
  String get cancel => 'Cancelar';

  @override
  String get ok => 'Aceptar';

  @override
  String get apply => 'Aplicar';

  @override
  String get readReplaceTitle => '¿Reemplazar la lista de canales actual?';

  @override
  String get readReplaceBody =>
      'Al leer los canales de la radio se reemplazará la lista de canales actual. Guárdela primero como CSV si quiere conservarla.';

  @override
  String get readChannels => 'Leer canales';

  @override
  String get radioReadyToReceive => 'La radio está lista para recibir';

  @override
  String get radioReady => 'La radio está lista';

  @override
  String beforeReading(String model) {
    return 'Antes de leer $model';
  }

  @override
  String beforeWriting(String model) {
    return 'Antes de escribir en $model';
  }

  @override
  String get readingProgress =>
      'Leyendo los canales de la radio: no la desconecte...';

  @override
  String get writingProgress => 'Escribiendo en la radio: no la desconecte…';

  @override
  String get writingSettingsProgress =>
      'Escribiendo los ajustes de la radio: no la desconecte...';

  @override
  String writeUnavailableTitle(String model) {
    return 'La escritura en $model aún no está disponible';
  }

  @override
  String get writeUnavailableBody =>
      'NewChirp puede leer esta radio, pero la escritura seguirá desactivada hasta que se haya probado y comprobado en una radio real. Así se evita que una escritura sin probar dañe la configuración de su radio.\n\nAún puede leer la radio, editar los canales y guardarlos o exportarlos. Si puede ayudar a probar la escritura, envíe un informe de error e indíquelo.';

  @override
  String get incompatibleTitle => 'Algunos canales son incompatibles';

  @override
  String incompatibleSummary(int invalid, int total) {
    return '$invalid de $total canales no se pueden escribir en esta radio.';
  }

  @override
  String incompatibleMore(int count) {
    return '…y $count más.';
  }

  @override
  String incompatibleSkipHint(int count) {
    return 'Puede omitir los canales incompatibles y escribir los otros $count.';
  }

  @override
  String get reviewChannels => 'Revisar canales';

  @override
  String get skipAndWriteRemaining => 'Omitir y escribir el resto';

  @override
  String get writeChangesTitle => '¿Escribir estos cambios en la radio?';

  @override
  String get writeChannelsTitle => '¿Escribir estos canales en la radio?';

  @override
  String writeConfirmBody(int count, String model, String port) {
    return 'Se programarán $count canales en $model a través de $port. Mantenga la radio conectada y encendida.';
  }

  @override
  String get writeConfirmMappings =>
      'También se escribirán los cambios de bancos y zonas.';

  @override
  String writeConfirmIncompatible(int count) {
    return '$count canales incompatibles no se modificarán y se mostrarán después de la escritura.';
  }

  @override
  String get writeConfirmUppercase =>
      'Los nombres de canal en minúsculas se convertirán a mayúsculas, porque esta radio solo admite nombres en mayúsculas.';

  @override
  String get writeToRadio => 'Escribir en la radio';

  @override
  String applyTitle(String label) {
    return 'Aplicar $label';
  }

  @override
  String get applyIntro => 'Elija cómo añadir estos canales a la lista actual.';

  @override
  String get applyReplaceList => 'Reemplazar la lista de canales actual';

  @override
  String applyReplaceZone(String zone) {
    return 'Reemplazar los canales de la zona $zone';
  }

  @override
  String get applyReplaceListNote =>
      'Se perderán los cambios sin guardar de la lista actual.';

  @override
  String get applyReplaceZoneNote =>
      'Las demás zonas no cambian. Se perderán los cambios sin guardar de esta zona.';

  @override
  String get applyInsertAt => 'Insertar a partir del número de canal';

  @override
  String applyInsertNote(int count) {
    return 'Se sobrescribirán los canales del intervalo de $count canales.';
  }

  @override
  String get applyStartLabel => 'Número de canal inicial';

  @override
  String get applyStartError => 'Introduzca un número de canal de 1 o mayor.';

  @override
  String get settingsUnsaved => 'Cambios de ajustes sin guardar';

  @override
  String get settingsMatchRadio =>
      'Los ajustes coinciden con los últimos valores leídos de la radio.';

  @override
  String get settingsMatchSnapshot =>
      'Los ajustes coinciden con la copia guardada de la radio.';

  @override
  String get discardChanges => 'Descartar cambios';

  @override
  String get connectRadioToWrite => 'Conecte la radio para escribir';

  @override
  String get writeSettingsToRadio => 'Escribir ajustes en la radio';

  @override
  String get writeSettingsTitle => '¿Escribir estos ajustes en la radio?';

  @override
  String get writeSameSettingsTitle => '¿Escribir de nuevo los mismos ajustes?';

  @override
  String writeSettingsBody(int count, String model, String port) {
    return 'Se escribirán $count valores de ajustes en $model a través de $port. Mantenga la radio conectada y encendida.';
  }

  @override
  String writeSameSettingsBody(String model, String port) {
    return 'No ha cambiado nada desde la última lectura o escritura. NewChirp escribirá esta copia de la radio, con sus ajustes y sus canales, en $model a través de $port. Úselo para programar otra radio del mismo modelo. Mantenga la radio conectada y encendida.';
  }

  @override
  String get writeSettingsButton => 'Escribir ajustes';

  @override
  String get colBank => 'BANCO';

  @override
  String get colName => 'NOMBRE';

  @override
  String get colRxFrequency => 'FRECUENCIA RX';

  @override
  String get colToneMode => 'MODO DE TONO';

  @override
  String get colTxTone => 'TONO TX';

  @override
  String get colRxTone => 'TONO RX';

  @override
  String get colDtcs => 'DTCS';

  @override
  String get colRxDtcs => 'DTCS RX';

  @override
  String get colDtcsPol => 'POL. DTCS';

  @override
  String get colDuplex => 'DÚPLEX';

  @override
  String get colOffset => 'DESPLAZ. / FREC. TX';

  @override
  String get colCrossMode => 'MODO CRUZADO';

  @override
  String get colMode => 'MODO';

  @override
  String get colStep => 'PASO';

  @override
  String get colPower => 'POTENCIA';

  @override
  String get colScan => 'ESCANEO';

  @override
  String get colComment => 'COMENTARIO';

  @override
  String get helpNumber =>
      'Número de canal o posición de memoria guardada en la radio.';

  @override
  String get helpNumberMidland =>
      'Número de canal Midland. Las filas de repetidor se marcan como RPTR.';

  @override
  String get helpBank =>
      'Banco o zona al que pertenece según la radio seleccionada. Un borde verde marca el inicio de cada banco.';

  @override
  String get helpName => 'Nombre del canal guardado en la memoria de la radio.';

  @override
  String get helpRxFrequency =>
      'Frecuencia de recepción: la frecuencia que escucha la radio.';

  @override
  String get helpToneMode =>
      'Modo de silenciador de recepción/transmisión. Tone es CTCSS, TSQL es silenciador por tono, DTCS es un código digital y Cross usa tonos distintos.';

  @override
  String get helpTxTone =>
      'Tono CTCSS de transmisión en hercios. TSQL usa el mismo tono CTCSS para transmitir y recibir.';

  @override
  String get helpRxTone =>
      'Tono CTCSS de recepción en hercios. Primero ponga el modo de tono en TSQL o en un modo Cross adecuado.';

  @override
  String get helpDtcs => 'Código de silenciador digital DTCS de transmisión.';

  @override
  String get helpRxDtcs => 'Código de silenciador digital DTCS de recepción.';

  @override
  String get helpDtcsPol =>
      'Polaridad DTCS: normal o invertida para transmisión y recepción.';

  @override
  String get helpDuplex =>
      'Relación entre transmisión y recepción. Símplex usa una sola frecuencia; los desplazamientos o el modo split usan otra frecuencia de transmisión.';

  @override
  String get helpOffset =>
      'Desplazamiento de frecuencia, o la frecuencia de transmisión independiente en modo split.';

  @override
  String get helpCrossMode =>
      'Modos de tono/código distintos para recepción y transmisión, usados con Cross.';

  @override
  String get helpMode =>
      'Modulación de voz: FM, FM de banda estrecha o AM, según la radio.';

  @override
  String get helpStep => 'Tamaño del paso de sintonía en kHz.';

  @override
  String get helpPower => 'Nivel de potencia de transmisión seleccionado.';

  @override
  String get helpScan => 'Si el canal se incluye en el escaneo.';

  @override
  String get helpComment =>
      'Notas libres guardadas con el canal, si la radio lo admite.';

  @override
  String get helpExtra =>
      'Ajuste de canal propio de esta radio, informado por el controlador de CHIRP.';

  @override
  String get dragToReorder => 'Arrastre para reordenar la columna';

  @override
  String get editorTitle => 'Detalles del canal';

  @override
  String get editorSave => 'Guardar canal';

  @override
  String editorBulkTitle(int count) {
    return 'Editar $count canales';
  }

  @override
  String editorBulkSave(int count) {
    return 'Actualizar $count';
  }

  @override
  String get tipAbbreviations => 'Abreviaturas y términos';

  @override
  String get tipResetRepeater => 'Restablecer repetidor';

  @override
  String get tipDeleteChannel => 'Eliminar canal';

  @override
  String get tipCloseEditor => 'Cerrar editor';

  @override
  String get fieldChannel => 'Canal';

  @override
  String get fieldLocation => 'Posición';

  @override
  String get fieldName => 'Nombre';

  @override
  String get fieldReceiveChannel => 'Canal de recepción';

  @override
  String get fieldReceiveFrequency => 'Frecuencia de recepción (MHz)';

  @override
  String get fieldDuplex => 'Dúplex';

  @override
  String get fieldTxFrequency => 'Frecuencia TX';

  @override
  String get fieldOffset => 'Desplazamiento (MHz)';

  @override
  String get fieldToneMode => 'Modo de tono';

  @override
  String get fieldCrossMode => 'Modo cruzado';

  @override
  String get fieldCtcssTone => 'Tono CTCSS (Hz)';

  @override
  String get fieldTransmitTone => 'Tono de transmisión (Hz)';

  @override
  String get fieldReceiveTone => 'Tono de recepción (Hz)';

  @override
  String get fieldDtcsCode => 'Código DTCS';

  @override
  String get fieldTransmitDtcs => 'DTCS de transmisión';

  @override
  String get fieldReceiveDtcs => 'DTCS de recepción';

  @override
  String get fieldDtcsPolarity => 'Polaridad DTCS (TX / RX)';

  @override
  String get fieldMode => 'Modo';

  @override
  String get fieldStep => 'Paso (kHz)';

  @override
  String get fieldScan => 'Escaneo';

  @override
  String get fieldTransmitPower => 'Potencia de transmisión';

  @override
  String get fieldComment => 'Comentario';

  @override
  String get radioSpecificSettings => 'Ajustes de canal propios de esta radio';

  @override
  String get gm32ReceiveOnly =>
      'Esta frecuencia es solo de recepción. La GM-32 transmite en los canales GMRS.';

  @override
  String get choiceNone => 'Ninguno';

  @override
  String get choiceToneSquelch => 'Silenciador por tono';

  @override
  String get choiceSimplex => 'Símplex';

  @override
  String get choicePlusShift => 'Desplazamiento +';

  @override
  String get choiceMinusShift => 'Desplazamiento −';

  @override
  String get choiceSplit => 'Split';

  @override
  String get choiceTxOff => 'TX desactivada';

  @override
  String get choiceDtcsToNone => 'DTCS → Ninguno';

  @override
  String get choiceNoneToDtcs => 'Ninguno → DTCS';

  @override
  String get choiceNoneToTone => 'Ninguno → Tone';

  @override
  String get choiceNormalNormal => 'Normal / Normal';

  @override
  String get choiceNormalReverse => 'Normal / Invertida';

  @override
  String get choiceReverseNormal => 'Invertida / Normal';

  @override
  String get choiceReverseReverse => 'Invertida / Invertida';

  @override
  String get choiceDigitalVoice => 'Voz digital';

  @override
  String get connIntro =>
      'Primero lea los canales de la radio, edítelos en la biblioteca y después escriba de vuelta la imagen verificada.';

  @override
  String moduleLoaded(String name) {
    return 'Módulo experimental de CHIRP cargado: $name';
  }

  @override
  String get unload => 'Descargar';

  @override
  String get step1Title => 'Elija un cable de programación';

  @override
  String get step1Help =>
      'NewChirp detecta automáticamente las interfaces de programación USB serie y de almacenamiento masivo. Elija la que corresponde a la conexión de su radio. Si no aparece ninguna, conecte la radio y pulse actualizar.';

  @override
  String get programmingInterface => 'Interfaz de programación';

  @override
  String get refreshInterfaces => 'Actualizar interfaces';

  @override
  String get refreshHelp =>
      'Vuelve a buscar en el sistema interfaces de programación USB serie y de almacenamiento masivo. Si su radio no aparece, conéctela y pulse actualizar.';

  @override
  String get noInterface =>
      'No se ha detectado ninguna interfaz de programación. Conecte la radio y elija actualizar.';

  @override
  String get step2Title => 'Elija el modelo exacto de radio';

  @override
  String get step2Help =>
      'Cargue el catálogo de radios compatibles y seleccione el modelo exacto. Usar un modelo equivocado puede dañar la configuración de una radio. Los cables de programación no identifican la radio conectada, así que NewChirp no adivina el modelo. Si ya existe una imagen guardada de este modelo, la escritura se habilita sin volver a leer.';

  @override
  String get loadCatalog => 'Cargar el catálogo de radios compatibles';

  @override
  String get loadCatalogHelp =>
      'Obtiene la lista de modelos de radio compatibles con los controladores de CHIRP incluidos. Seleccione el modelo exacto antes de leer o escribir.';

  @override
  String get step3Title => 'Transfiera con seguridad';

  @override
  String get step3Help =>
      'Leer canales descarga la imagen completa de la memoria de la radio, reemplaza la lista de canales actual y guarda la imagen para este modelo. Los ajustes de la radio se leen aparte, en la página Ajustes de la radio. Escribir envía la lista de canales actual usando la imagen guardada. Mantenga la radio conectada y encendida durante cualquiera de las dos transferencias.';

  @override
  String get readChannelsFromRadio => 'Leer canales de la radio';

  @override
  String get imageNone =>
      'Aún no hay imagen de este modelo. Lea la radio una vez para habilitar la escritura.';

  @override
  String imageStored(String model) {
    return 'La imagen guardada de $model está lista. Puede escribir sin volver a leer.';
  }

  @override
  String get imageSession =>
      'Se ha leído una imagen de la radio en esta sesión. Revise todos los cambios antes de escribir.';

  @override
  String get pickerSemanticsChoose => 'Elegir modelo de radio';

  @override
  String pickerSemanticsSelected(String model) {
    return 'Radio seleccionada: $model';
  }

  @override
  String get pickerLabel => 'Modelo de radio';

  @override
  String pickerHint(int count) {
    return 'Elija entre $count radios compatibles';
  }

  @override
  String get pickerTitle => 'Elija su radio';

  @override
  String get pickerSubtitle =>
      'Explore por fabricante o busque en el catálogo completo.';

  @override
  String get close => 'Cerrar';

  @override
  String get pickerSearchHint =>
      'Busque por fabricante o modelo, p. ej. Icom ID-52';

  @override
  String get clearSearch => 'Borrar búsqueda';

  @override
  String get pickerNoMatch =>
      'Ningún modelo de radio coincide con esta búsqueda.';

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
  String get pickerAllVendors => 'Todos los fabricantes';

  @override
  String get pickerRecent => 'Recientes';

  @override
  String get selected => 'Seleccionada';

  @override
  String get edited => '• Editado';

  @override
  String moduleActive(String name) {
    return 'Módulo experimental de CHIRP: $name';
  }

  @override
  String get menuNew => 'Nuevo';

  @override
  String get newBlank => 'Configuración en blanco';

  @override
  String get newGmrs => 'Plantilla inicial GMRS';

  @override
  String get newMarine => 'Plantilla VHF marina';

  @override
  String get newRestoreStock => 'Restaurar canales de fábrica';

  @override
  String get openChannelFile => 'Abrir archivo de canales';

  @override
  String get loadModule => 'Cargar módulo de controlador de CHIRP…';

  @override
  String get loadModuleShort => 'Cargar controlador…';

  @override
  String get unloadModule => 'Descargar módulo de CHIRP';

  @override
  String get save => 'Guardar';

  @override
  String get saveAs => 'Guardar como…';

  @override
  String get printChannelList => 'Imprimir lista de canales…';

  @override
  String get print => 'Imprimir';

  @override
  String get help => 'Ayuda';

  @override
  String get reportProblem => 'Informar de un problema…';

  @override
  String get checkingUpdates => 'Buscando actualizaciones...';

  @override
  String get checkUpdates => 'Buscar actualizaciones';

  @override
  String get showSummary => 'Mostrar resumen de canales';

  @override
  String get hideSummary => 'Ocultar el resumen para ver más canales';

  @override
  String get metricChannels => 'Canales';

  @override
  String get metricScan => 'Con escaneo';

  @override
  String get metricAttention => 'Requieren atención';

  @override
  String get editBanksZones => 'Editar bancos / zonas';

  @override
  String get banksZonesTitle => 'Bancos y zonas';

  @override
  String get banksZonesHelp =>
      'Use este editor para cambiar el nombre de zonas o bancos y elegir qué memorias de canal pertenecen a cada uno. Algunas radios permiten un canal en varias zonas. Una entrada vacía «Nueva zona» se crea al añadirle un canal. Los cambios se escriben junto con los canales; revíselos antes de escribir, porque la pertenencia sigue al número de memoria del canal.';

  @override
  String get radioSection => 'Sección de la radio';

  @override
  String zoneChannelCount(String name, int count) {
    return '$name ($count canales)';
  }

  @override
  String get radioSectionsTitle => 'Secciones de la radio';

  @override
  String get radioSectionsHelp =>
      'Esta radio tiene secciones de canales o subdispositivos separados. Elija una sección para ver y editar sus canales. Al escribir se conservan las demás secciones de la imagen guardada de la radio. Los bancos y zonas se editan aparte.';

  @override
  String get search => 'Buscar';

  @override
  String get searchHint => 'Buscar nombre, frecuencia o nota';

  @override
  String get clearChannelSearch => 'Borrar búsqueda de canales';

  @override
  String bulkEditTip(int count) {
    return 'Editar a la vez $count canales seleccionados';
  }

  @override
  String clearSelectedTip(int count) {
    return 'Vaciar $count canales seleccionados';
  }

  @override
  String get duplicateChannel => 'Duplicar canal';

  @override
  String get addChannel => 'Añadir canal';

  @override
  String get slots => 'Posiciones';

  @override
  String get showEmptySlotsTip =>
      'Mostrar todas las posiciones de memoria, incluidas las vacías';

  @override
  String get clearColumnFilters => 'Borrar filtros de columnas';

  @override
  String editSelected(int count) {
    return 'Editar $count seleccionados';
  }

  @override
  String get duplicate => 'Duplicar';

  @override
  String get showEmptySlots => 'Mostrar posiciones vacías';

  @override
  String get clearFilters => 'Borrar filtros';

  @override
  String get openShort => 'Abrir…';

  @override
  String get welcomeTitle => '¿Qué quiere hacer?';

  @override
  String get welcomeSubtitle =>
      'Abra un archivo de CHIRP existente o lea los canales directamente de su radio.';

  @override
  String get welcomeLoadTitle => 'Cargar configuración';

  @override
  String get welcomeLoadBody =>
      'Abra un CSV de CHIRP o un archivo de imagen nativo y siga editando.';

  @override
  String get welcomeLoadHelp =>
      'Abra un CSV compatible con CHIRP o una imagen nativa de radio. Las imágenes nativas conservan el modelo seleccionado y la imagen guardada necesarios para transferir a la radio.';

  @override
  String get welcomeReadTitle => 'Leer canales de una radio';

  @override
  String get welcomeReadBody =>
      'Conecte un cable de programación e importe los canales actuales de la radio.';

  @override
  String get welcomeConnect => 'Conectar radio';

  @override
  String get welcomeReadHelp =>
      'Abra la pantalla de conexión de la radio, elija su cable y el modelo exacto y después elija Leer canales de la radio. Los ajustes se leen aparte, en la página Ajustes de la radio.';

  @override
  String get welcomeRepeatersTitle => 'Buscar repetidores cercanos';

  @override
  String get welcomeRepeatersBody =>
      'Busque en RepeaterBook y añada canales de repetidores.';

  @override
  String get welcomeRepeatersHelp =>
      'Busque repetidores de radioaficionado y GMRS en RepeaterBook, vea los que coinciden y añada los canales seleccionados a la biblioteca actual.';

  @override
  String get welcomeTip =>
      'Para escribir en una radio, primero hay que leer de ella una imagen del mismo modelo. Puede planificar o editar un CSV en cualquier momento, pero la escritura en la radio sigue bloqueada hasta completar una lectura.';

  @override
  String get updateCheckFailed => 'No se pudieron buscar actualizaciones';

  @override
  String get updateCheckFailedHint =>
      'También puede descargar la última versión desde newchirp.net.';

  @override
  String get aboutSubtitle =>
      'Información de la aplicación y licencias de código abierto';

  @override
  String get freqRefTitle => 'Referencia de frecuencias';

  @override
  String get freqRefUsSubtitle =>
      'Plan de canales FRS/GMRS de EE. UU. (Parte 95)';

  @override
  String get settingsSubtitle =>
      'Opciones generales de la radio que ofrece el controlador seleccionado';

  @override
  String aboutTagline(String version) {
    return 'Programador de radios de escritorio · Versión $version';
  }

  @override
  String get contributor => 'Colaborador';

  @override
  String get chirpLayerTitle => 'Capa de compatibilidad con CHIRP';

  @override
  String get chirpLayerBody1 =>
      'NewChirp usa los controladores de CHIRP para la compatibilidad con las radios. Los derechos de autor de CHIRP pertenecen a sus colaboradores, y CHIRP es software libre con licencia GNU General Public License, versión 3 o (a su elección) cualquier versión posterior.';

  @override
  String get chirpLayerBody2 =>
      'NewChirp también desarrolla sus propios controladores para radios que aún no tienen controlador en CHIRP o cuyo controlador de CHIRP no funciona bien. Estos controladores mantenidos por NewChirp se publican bajo GPLv3 o posterior y pueden incorporarse a CHIRP con la misma licencia, sujeto a la revisión y aceptación de sus mantenedores.';

  @override
  String chirpSource(String url) {
    return 'Proyecto y código fuente de CHIRP: $url';
  }

  @override
  String newchirpSource(String url) {
    return 'Proyecto y código fuente de NewChirp: $url';
  }

  @override
  String get licensesTitle => 'Licencias de código abierto';

  @override
  String get licensesBody =>
      'El texto completo de la GPL de CHIRP y las licencias de pySerial, libusb y las dependencias de Flutter se incluyen con esta aplicación.';

  @override
  String get viewLicenses => 'Ver licencias completas';

  @override
  String get notAffiliated =>
      'NewChirp es una interfaz independiente y no está afiliada ni respaldada por el proyecto CHIRP.';

  @override
  String get settingsIntro =>
      'Ajuste opciones generales de la radio, como el silenciador, la retroiluminación, el VOX y otros controles que ofrece el controlador de CHIRP seleccionado.';

  @override
  String get settingsNoModel =>
      'No hay ningún modelo de radio seleccionado. Abra primero Conexión de la radio.';

  @override
  String get settingsNoCable => 'Ningún cable de programación seleccionado';

  @override
  String get settingsReadFromRadio => 'leídos de la radio';

  @override
  String get settingsSnapshotAvailable => 'copia guardada disponible';

  @override
  String get settingsLoading => 'Cargando los ajustes de la radio...';

  @override
  String get settingsUnsupportedTitle =>
      'Esta radio no ofrece ajustes generales';

  @override
  String get settingsUnsupportedBody =>
      'El controlador de CHIRP seleccionado no ofrece ajustes generales de la radio. Los ajustes de cada canal siguen disponibles en el editor de canales.';

  @override
  String get settingsLoadError =>
      'No se pudieron cargar los ajustes de la radio';

  @override
  String get settingsReadTitle => 'Leer los ajustes de la radio';

  @override
  String get settingsReadBodyConnected =>
      'Lea los ajustes actuales directamente de la radio conectada. Solo se actualizan la copia guardada y los ajustes; la lista de canales actual no cambia.';

  @override
  String get settingsReadBodyDisconnected =>
      'Seleccione el cable de programación y el modelo exacto en Conexión de la radio y después lea la radio para cargar sus ajustes.';

  @override
  String get openRadioConnection => 'Abrir conexión de la radio';

  @override
  String get settingsNotLoadedTitle => 'Los ajustes aún no se han cargado';

  @override
  String get settingsNotLoadedConnected =>
      'Lea los valores actuales de la radio conectada o use la copia guardada de la radio para ver los valores almacenados.';

  @override
  String get settingsNotLoadedSnapshot =>
      'Use la copia guardada de la radio para cargar los valores almacenados.';

  @override
  String get readSettingsFromRadio => 'Leer los ajustes actuales de la radio';

  @override
  String get useSavedSnapshot => 'Usar la copia guardada de la radio';

  @override
  String uiDefaultsComeFromChannelOnlyFields(Object p0) {
    return 'Los valores iniciales vienen del canal $p0. Solo los campos que cambie aquí se aplicarán a todos los canales seleccionados.';
  }

  @override
  String get uiSelectedChannelsNeedChanges =>
      'Los canales seleccionados necesitan cambios';

  @override
  String get uiBackToEditor => 'Volver al editor';

  @override
  String uiUpdatedSelectedChannels(Object p0) {
    return 'Se actualizaron $p0 canales seleccionados';
  }

  @override
  String uiConnectTheAndChooseItsPort(Object p0, Object p1) {
    return 'Conecte la $p0 y elija su puerto para leer $p1.';
  }

  @override
  String get uiBankAndZoneChangesAreReady =>
      'Los cambios de bancos y zonas están listos. Escríbalos junto con los canales.';

  @override
  String get uiCouldnTCompleteThatAction => 'No se pudo completar esa acción';

  @override
  String get uiMoreInfo => 'Más información:';

  @override
  String get uiSubmitBugReport => 'Enviar informe de error';

  @override
  String get uiLoadExperimentalChirpModule =>
      '¿Cargar un módulo experimental de CHIRP?';

  @override
  String get uiChirpModulesAreExecutablePythonCode =>
      'Los módulos de CHIRP son código Python ejecutable. NewChirp ejecuta el módulo en un entorno aislado que bloquea su carpeta personal, otras unidades y la red. Aun así, el módulo puede usar la radio seleccionada y los archivos de esta sesión.';

  @override
  String get uiOnlyLoadAModuleFromA =>
      'Cargue módulos solo de fuentes de confianza. Un módulo defectuoso puede dañar la radio. El módulo solo está activo durante esta sesión de NewChirp. Seleccione el modelo de radio y vuelva a leer la radio antes de escribir.';

  @override
  String get uiLoadModule => 'Cargar módulo';

  @override
  String uiMovedToChannel(Object p0, Object p1) {
    return '$p0 se movió al canal $p1';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations =>
      'Esta radio tiene posiciones de canal fijas, así que no se pueden insertar posiciones vacías.';

  @override
  String uiInsertedAnEmptySlotBeforeChannel(Object p0) {
    return 'Se insertó una posición vacía antes del canal $p0';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations2 =>
      'Esta radio tiene posiciones de canal fijas, así que no se pueden quitar posiciones vacías.';

  @override
  String uiRemovedEmptySlot(Object p0) {
    return 'Se quitó la posición vacía $p0';
  }

  @override
  String get uiRepeaterbookResults => 'resultados de RepeaterBook';

  @override
  String get uiMacosBlockedTheSaveLocation =>
      'macOS bloqueó la ubicación de guardado';

  @override
  String get uiNewchirpDoesNotHavePermissionTo =>
      'NewChirp no tiene permiso para escribir en esta carpeta. Elija otra carpeta ahora, o permita el acceso a NewChirp en Ajustes del Sistema > Privacidad y seguridad > Archivos y carpetas.';

  @override
  String get uiChooseAnotherFolder => 'Elegir otra carpeta';

  @override
  String uiStart(Object p0) {
    return '¿Empezar $p0?';
  }

  @override
  String get uiKeepCurrentList => 'Conservar la lista actual';

  @override
  String get uiDiscardAndContinue => 'Descartar y continuar';

  @override
  String uiMarineVhfTemplate(Object p0) {
    return 'Plantilla VHF marina: $p0';
  }

  @override
  String get uiStockChannels => 'canales de fábrica';

  @override
  String get uiDiscardUnsavedSettingsChanges =>
      '¿Descartar los cambios de ajustes sin guardar?';

  @override
  String get uiUsingTheSavedRadioSnapshotWill =>
      'Usar la copia guardada de la radio reemplazará los cambios de ajustes sin guardar de esta página.';

  @override
  String get uiUseSavedSnapshot => 'Usar la copia guardada';

  @override
  String get uiReplaceUnsavedSettingsChanges =>
      '¿Reemplazar los cambios de ajustes sin guardar?';

  @override
  String get uiReadingSettingsFromTheRadioWill =>
      'Leer los ajustes de la radio reemplazará los cambios de ajustes sin guardar de esta página. La lista de canales actual no cambia.';

  @override
  String get uiReadSettings => 'Leer ajustes';

  @override
  String get uiWhereShouldTheNewChannelGo => '¿Dónde debe ir el nuevo canal?';

  @override
  String get uiAtTheEnd => 'Al final';

  @override
  String get uiBeforeTheSelectedChannel => 'Antes del canal seleccionado';

  @override
  String get uiAfterTheSelectedChannel => 'Después del canal seleccionado';

  @override
  String uiChannelAdded(Object p0) {
    return 'Canal $p0 añadido';
  }

  @override
  String get uiThisRadioHasFixedChannelLocations3 =>
      'Esta radio tiene posiciones de canal fijas. Los canales nuevos solo pueden añadirse después del último canal.';

  @override
  String uiOverwriteChannels(Object p0) {
    return '¿Sobrescribir $p0 canales?';
  }

  @override
  String uiTheDestinationRangeThroughContainsChannels(
    Object p0,
    Object p1,
    Object p2,
  ) {
    return 'El intervalo de destino de $p0 a $p1 contiene $p2 canales con datos. Al pegar se reemplazarán.';
  }

  @override
  String get uiOverwriteChannels2 => 'Sobrescribir canales';

  @override
  String uiOverwriteChannel(Object p0) {
    return '¿Sobrescribir el canal $p0?';
  }

  @override
  String get uiOverwriteChannel2 => 'Sobrescribir canal';

  @override
  String uiClearedChannelsUseCmdCtrlZ(Object p0) {
    return 'Se vaciaron $p0 canales. Use Cmd/Ctrl+Z para deshacer.';
  }

  @override
  String uiStaysInTheRadioTheName(Object p0) {
    return '$p0 se queda en la radio. Se borra el nombre y vuelve la frecuencia del repetidor sin cambios.';
  }

  @override
  String uiAndMoreChannels(Object p0) {
    return '…y $p0 canales más.';
  }

  @override
  String get uiNamesAreConvertedOnlyWhenThe =>
      'Los nombres solo se convierten cuando la radio seleccionada lo exige. Las frecuencias personalizadas pueden necesitar un canal fuera del rango de memoria bloqueado de la radio.';

  @override
  String get uiStopWritingTheRadio => '¿Detener la escritura en la radio?';

  @override
  String get uiTheRadioIsBeingWrittenNow =>
      'Se está escribiendo en la radio. Algunas radios tardan uno o dos minutos, y el tiempo transcurrido indica que la escritura sigue en curso. Detenerla a medias puede dejar parte de la memoria de la radio a medio escribir; entonces puede ser necesario apagarla y encenderla y volver a escribir.';

  @override
  String get uiStopAnyway => 'Detener de todos modos';

  @override
  String get uiKeepWriting => 'Seguir escribiendo';

  @override
  String get uiLater => 'Más tarde';

  @override
  String get uiOpenDownloadPage => 'Abrir la página de descarga';

  @override
  String get uiDownloadAndInstall => 'Descargar e instalar';

  @override
  String get uiFinishTheCurrentOperationFirst =>
      'Termine primero la operación en curso';

  @override
  String get uiWaitForTheCurrentRadioOr =>
      'Espere a que termine la operación actual con la radio o con archivos antes de instalar NewChirp.';

  @override
  String get uiSaveRadioSettingsFirst =>
      'Guarde primero los ajustes de la radio';

  @override
  String get uiYouHaveRadioSettingChangesThat =>
      'Tiene cambios en los ajustes de la radio que no se han escrito. Guárdelos antes de instalar la actualización.';

  @override
  String get uiSaveYourChannelChangesFirst =>
      'Guarde primero los cambios de canales';

  @override
  String get uiNewchirpWillCloseToInstallThe =>
      'NewChirp se cerrará para instalar la actualización. Guarde la lista de canales actual antes de continuar.';

  @override
  String get uiSaveAndContinue => 'Guardar y continuar';

  @override
  String get uiInstallingNewchirpUpdate =>
      'Instalando la actualización de NewChirp';

  @override
  String get uiNewchirpWillCloseAndReopenAutomatically =>
      'NewChirp se cerrará y se volverá a abrir automáticamente cuando el instalador esté listo.';

  @override
  String get uiUpdateCouldNotBeInstalled =>
      'No se pudo instalar la actualización';

  @override
  String uiYouCanStillDownloadTheLatest(Object p0) {
    return '$p0\n\nAún puede descargar la última versión desde newchirp.net.';
  }

  @override
  String get uiCouldnTOpenYourBrowser => 'No se pudo abrir el navegador';

  @override
  String uiNewchirpCouldNotStartTheBrowser(Object p0) {
    return 'NewChirp no pudo abrir el navegador en este equipo. Abra usted mismo esta dirección para obtener la actualización:\n\n$p0';
  }

  @override
  String get uiCopyLink => 'Copiar enlace';

  @override
  String get uiYouReUpToDate => 'Está al día';

  @override
  String uiNewchirpIsTheLatestVersion(Object p0) {
    return 'NewChirp $p0 es la versión más reciente.';
  }

  @override
  String uiChannelIsOccupied(Object p0) {
    return 'El canal $p0 está ocupado';
  }

  @override
  String get uiReplace => 'Reemplazar';

  @override
  String get uiSwap => 'Intercambiar';

  @override
  String get uiMoveAndShift => 'Mover y desplazar';

  @override
  String uiChannelsScanEnabledNeedAttention(Object p0, Object p1, Object p2) {
    return '$p0 canales · $p1 con escaneo · $p2 requieren atención';
  }

  @override
  String get uiReview => 'Revisar';

  @override
  String get uiNoRadioImageLoadedEditingAnd =>
      'No hay ninguna imagen de radio cargada. Puede editar y exportar a CSV, pero la escritura sigue bloqueada hasta que lea esta radio.';

  @override
  String get uiChannelEditing => 'Edición de canales';

  @override
  String get uiAddLetsYouPlaceANew =>
      'Añadir le permite colocar un canal nuevo al final, antes del canal seleccionado o después. Antes y Después desplazan los canales siguientes por las posiciones de memoria de la radio. Duplicar copia la fila seleccionada, y Eliminar la quita tras confirmarlo. Haga doble clic en cualquier fila para editar todos sus campos. Haga clic derecho en una fila para copiarla, cortarla, pegarla, duplicarla o vaciarla. Al copiar o cortar una selección de varias filas se copian los canales activos como un bloque; al pegar, el bloque se coloca en la fila de destino. Un clic selecciona una fila. Mayús+clic selecciona un intervalo, y Cmd/Ctrl+clic marca o desmarca filas sueltas. Use Edición múltiple para cambiar propiedades en todas las filas seleccionadas; solo se aplican los campos que modifique. Haga clic derecho y elija Propiedades para abrir el mismo editor. Arrastre el asa del borde izquierdo de una fila para moverla; los canales intermedios se desplazan por las mismas posiciones de memoria. Mostrar posiciones vacías mantiene visible la distribución de la memoria de la radio; haga doble clic en una posición vacía para crear un canal en ella. Vaciar quita de la radio la fila seleccionada, o todas las filas seleccionadas, en la próxima escritura. Use Cmd/Ctrl+Z para deshacer y Cmd/Ctrl+Mayús+Z para rehacer.';

  @override
  String get uiChooseAPrinter => 'Elija una impresora';

  @override
  String get uiPrintJobSent => 'Trabajo de impresión enviado';

  @override
  String uiWasSentTo(Object p0, Object p1) {
    return '$p0 se envió a $p1.';
  }

  @override
  String get uiUsFrsGmrs => 'FRS / GMRS de EE. UU.';

  @override
  String uiReferenceSourceVerifyCurrentNationalRules(Object p0) {
    return 'Fuente de referencia: $p0 Compruebe la normativa nacional vigente antes de transmitir.';
  }

  @override
  String get uiGmrsFrsFrequencyReference =>
      'Referencia de frecuencias GMRS y FRS';

  @override
  String get uiUnitedStatesPartChannelPlanColor =>
      'Plan de canales de la Parte 95 de EE. UU., con colores por banda de frecuencia y clase de potencia.';

  @override
  String get uiRepeaterPairsGmrsOnly => 'Pares de repetidor (solo GMRS)';

  @override
  String get uiKeyNotes => 'Notas importantes';

  @override
  String get uiAllFrequenciesAreInMhzGmrs =>
      'Todas las frecuencias están en MHz. GMRS requiere una licencia de la FCC; FRS no necesita licencia individual.\nLas radios GMRS móviles o de base no pueden transmitir en los canales 8-14. Las entradas de repetidor son solo GMRS.\nPor costumbre, el canal 20 (462,675 MHz) con CTCSS 141,3 Hz se usa a menudo como canal de viaje y asistencia.\nSolo como referencia: compruébelo con la normativa vigente de la Parte 95 de la FCC y el manual de su radio.';

  @override
  String get uiNoEditableOptionsInThisGroup =>
      'No hay opciones editables en este grupo.';

  @override
  String get uiKeepTheRadioPoweredOnAnd =>
      'Mantenga la radio encendida y el cable conectado.';

  @override
  String uiThisSettingTypeIsNotSupported(Object p0) {
    return '$p0: este tipo de ajuste aún no es compatible.';
  }

  @override
  String get uiSearchAbbreviationsOrDefinitions =>
      'Buscar abreviaturas o definiciones';

  @override
  String get uiNoMatchingTerms => 'No hay términos que coincidan.';

  @override
  String get uiThanksTheDiagnosticLogAndError =>
      'Gracias. El registro de diagnóstico y los detalles del error se enviaron al desarrollador de NewChirp.';

  @override
  String get uiYourEmail => 'Su correo electrónico';

  @override
  String get uiUsedOnlyIfTheDeveloperNeeds =>
      'Solo se usa si el desarrollador necesita más información.';

  @override
  String get uiWhatWereYouTryingToDo => '¿Qué intentaba hacer?';

  @override
  String get uiTheReportIncludesAppAndOperating =>
      'El informe incluye las versiones de la aplicación y del sistema operativo, la radio y el puerto serie seleccionados y los eventos de diagnóstico recientes. No se registra el contenido de los canales ni los archivos cargados.';

  @override
  String uiPreviewDiagnosticEvents(Object p0) {
    return 'Ver $p0 eventos de diagnóstico';
  }

  @override
  String uiFilterCounties(Object p0) {
    return 'Filtrar condados de $p0';
  }

  @override
  String get uiFindACounty => 'Buscar un condado';

  @override
  String uiOfCounties(Object p0, Object p1) {
    return '$p0 de $p1 condados';
  }

  @override
  String get uiClearAll => 'Quitar todo';

  @override
  String get uiNoMatchingCounties => 'No hay condados que coincidan.';

  @override
  String get uiNoCoordinatesAreAvailableForThese =>
      'No hay coordenadas disponibles para estos resultados.';

  @override
  String uiMappedTapAPinToSelect(Object p0) {
    return '$p0 en el mapa • toque un marcador para seleccionarlo';
  }

  @override
  String get uiSearchARepeaterDirectoryAndAdd =>
      'Busque en un directorio de repetidores y añada los canales seleccionados a su biblioteca actual. Compruebe el estado y el acceso del repetidor antes de transmitir.';

  @override
  String get uiDirectory => 'Directorio';

  @override
  String get uiMygmrsRequiresAnActiveGmrsLicense =>
      'myGMRS exige una licencia GMRS activa para ver las frecuencias de repetidores. Los tonos PL y las normas requieren una suscripción Premium. Esta sesión dura hasta que se cierre NewChirp.';

  @override
  String get uiCountry => 'País';

  @override
  String get uiSortResults => 'Ordenar resultados';

  @override
  String get uiSourceOrder => 'Orden de la fuente';

  @override
  String get uiFrequency => 'Frecuencia';

  @override
  String get uiCallsignName => 'Indicativo / nombre';

  @override
  String get uiCity => 'Ciudad';

  @override
  String get uiCounty => 'Condado';

  @override
  String get uiService => 'Servicio';

  @override
  String get uiAmateurGmrs => 'Radioaficionado + GMRS';

  @override
  String get uiAmateurHam => 'Radioaficionado';

  @override
  String get uiClearRepeaterSearch => 'Borrar búsqueda de repetidores';

  @override
  String get uiLatitudeOptional => 'Latitud (opcional)';

  @override
  String get uiLongitudeOptional => 'Longitud (opcional)';

  @override
  String get uiRadiusKm => 'Radio en km';

  @override
  String get uiOpenRepeatersOnly => 'Solo repetidores abiertos';

  @override
  String get uiFmCapableOnly => 'Solo con FM';

  @override
  String get uiSearchAmateurRepeatersInstead =>
      'Buscar repetidores de radioaficionado';

  @override
  String get uiFilterLoadedResults => 'Filtrar los resultados cargados';

  @override
  String get uiCityCountyCallsignModeServiceOr =>
      'Ciudad, condado, indicativo, modo, servicio o frecuencia';

  @override
  String get uiClearResultFilter => 'Borrar el filtro de resultados';

  @override
  String get uiList => 'Lista';

  @override
  String get uiMap => 'Mapa';

  @override
  String get uiSelectAll => 'Seleccionar todo';

  @override
  String get uiClear => 'Borrar';

  @override
  String get uiDataCourtesyOfRepeaterbookCom =>
      'Datos por cortesía de RepeaterBook.com.';

  @override
  String get uiDragToResize => 'Arrastre para cambiar el tamaño';

  @override
  String get uiInsertEmptySlotBefore => 'Insertar posición vacía antes';

  @override
  String get uiRemoveEmptySlot => 'Quitar posición vacía';

  @override
  String uiMove(Object p0) {
    return 'Mover $p0';
  }

  @override
  String get uiDragRowsToRearrangeChannels =>
      'Arrastre filas para reordenar los canales';

  @override
  String get uiFilter => 'Filtrar';

  @override
  String get uiNoMatchingChannels => 'No hay canales que coincidan';

  @override
  String get uiWriteChannelsToRadio => 'Escribir canales en la radio';

  @override
  String get uiThanksTheDiagnosticLogAndProblem =>
      'Gracias. El registro de diagnóstico y los detalles del problema se enviaron al desarrollador de NewChirp.';

  @override
  String get uiTheReportIncludesAppAndOperating2 =>
      'El informe incluye las versiones de la aplicación y del sistema operativo, la radio seleccionada, el firmware si está disponible, el puerto serie y los eventos de diagnóstico recientes. No se registra el contenido de los canales ni los archivos cargados.';

  @override
  String get uiSaveFile => 'Guardar archivo';

  @override
  String get uiDoNotShowMeThisMessage => 'No volver a mostrar este mensaje';

  @override
  String get uiMarineVhfChannelTemplate => 'Plantilla de canales VHF marinos';

  @override
  String get uiPlan => 'Plan';

  @override
  String uiSource(Object p0) {
    return 'Fuente: $p0';
  }

  @override
  String get uiTheChannelPlanIsSelectedBy =>
      'El plan de canales se elige por región reglamentaria, no por código postal. Las asignaciones de canales marinos son nacionales o internacionales y no cambian según el código postal.';

  @override
  String get uiProgramShipTransmitFrequencies =>
      'Programar frecuencias de transmisión de barco';

  @override
  String get uiReceiveOnlyIsTheSafeDefault =>
      'Solo recepción es la opción segura por defecto. Actívelo solo si la radio y la instalación están autorizadas para transmitir en VHF marina.';

  @override
  String get uiMostAmateurTransceiversAreNotType =>
      'La mayoría de los transceptores de radioaficionado no están homologados para transmitir en la banda marina. Los canales prohibidos y de solo recepción siguen con la transmisión desactivada.';

  @override
  String uiChannelsTransmitCapableReceiveOnly(Object p0, Object p1, Object p2) {
    return '$p0 canales: $p1 con transmisión, $p2 solo recepción.';
  }

  @override
  String get uiAllRowsWillBeAddedReceive =>
      'Todas las filas se añadirán como solo recepción (Duplex \"off\"). La radio pitará y no transmitirá en ellas. Marque la casilla de arriba para programar las frecuencias de transmisión.';

  @override
  String get uiContinue => 'Continuar';

  @override
  String get uiType => 'Tipo';

  @override
  String get uiThisRadioDoesNotExposeEditable =>
      'Esta radio no ofrece bancos editables.';

  @override
  String get uiTheseBanksAreFixedByThe =>
      'Estos bancos los fija la radio y se muestran como referencia.';

  @override
  String get uiUseTheseChanges => 'Usar estos cambios';

  @override
  String get uiFindAChannel => 'Buscar un canal';

  @override
  String uiChannel(Object p0) {
    return 'Canal $p0';
  }

  @override
  String get uiLoadingRadioCatalog => 'Cargando el catálogo de radios…';

  @override
  String get uiActionFailed => 'La acción falló';

  @override
  String uiMacosBlockedNewchirpFromWritingTo(Object p0) {
    return '$p0\n\nmacOS impidió que NewChirp escribiera en esa carpeta. Elija otra ubicación de guardado o permita el acceso a NewChirp en:\n\nAjustes del Sistema > Privacidad y seguridad > Archivos y carpetas > NewChirp\n\nConceda acceso a Documentos y vuelva a guardar.';
  }

  @override
  String uiOnLinuxThisUsuallyMeansYour(Object p0) {
    return '$p0\n\nEn Linux, esto suele significar que su usuario no tiene permiso para abrir el cable de programación de la radio.\n\nSolucionarlo con:\n    sudo usermod -aG dialout \$USER\n\nDespués cierre la sesión y vuelva a entrar, reconecte el cable e inténtelo de nuevo.\n\nSolo para la sesión de terminal actual:\n    newgrp dialout';
  }

  @override
  String get uiMototrboCpsChannels => 'canales de MOTOTRBO CPS 2.0';

  @override
  String get uiCsvChannels => 'canales CSV';

  @override
  String get uiRefreshingRadioCatalog => 'Actualizando el catálogo de radios…';

  @override
  String get uiThisChirpImage => 'esta imagen de CHIRP';

  @override
  String get uiNoEmptyChannelSlotIsAvailable =>
      'No hay ninguna posición de canal vacía disponible.';

  @override
  String get uiNoEmptyChannelSlotsAreAvailable =>
      'No hay posiciones de canal vacías disponibles en esta radio.';

  @override
  String get uiSavingChannelLibrary => 'Guardando la biblioteca de canales…';

  @override
  String get uiSaveCanceled => 'Guardado cancelado';

  @override
  String get uiDiscardTheCurrentChannelListAny =>
      '¿Descartar la lista de canales actual? Se perderán los cambios sin guardar.';

  @override
  String uiCloseTheCurrentChannelListAnd(Object p0) {
    return '¿Cerrar la lista de canales actual y empezar $p0?';
  }

  @override
  String get uiANewBlankConfiguration => 'una configuración en blanco';

  @override
  String get uiReadingRadioSettingsDoNotDisconnect =>
      'Leyendo los ajustes de la radio: no la desconecte...';

  @override
  String get uiSelectAChannelFirst => 'Seleccione primero un canal';

  @override
  String get uiThisRadioHasFixedChannelLocations4 =>
      'Esta radio tiene posiciones de canal fijas.';

  @override
  String uiAndFollowingChannelsMoveDownOne(Object p0) {
    return '$p0 y los canales siguientes bajan una posición.';
  }

  @override
  String uiUseChannelAfterTheFinalChannel(Object p0) {
    return 'Usar el canal $p0, después del último canal.';
  }

  @override
  String get uiTheCopiedChannelDoesNotFit =>
      'El canal copiado no cabe en la memoria de esta radio.';

  @override
  String get uiTheCopiedChannelsDoNotFit =>
      'Los canales copiados no caben a partir de esta fila.';

  @override
  String get uiThisChannelContainsDataPastingWill =>
      'Este canal contiene datos. Al pegar se reemplazarán.';

  @override
  String uiContainsDataPastingWillReplaceIt(Object p0) {
    return '«$p0» contiene datos. Al pegar se reemplazarán.';
  }

  @override
  String get uiLoadingRadioInstructions =>
      'Cargando las instrucciones de la radio…';

  @override
  String get uiRestoringChannelsFromTheStoredRadio =>
      'Restaurando los canales desde la imagen guardada de la radio…';

  @override
  String get uiSomeChannelsWereNotWritten =>
      'Algunos canales no se escribieron';

  @override
  String get uiSomeChannelValuesWereAdjusted =>
      'Se ajustaron algunos valores de canal';

  @override
  String uiTheWriteFinishedChannelsWereAdjusted(Object p0, Object p1) {
    return 'La escritura terminó. Se ajustaron $p0 canales y $p1 no se pudieron escribir.';
  }

  @override
  String uiTheCompatibleChannelsWereWrittenBut(Object p0) {
    return 'Se escribieron los canales compatibles, pero $p0 canales no se pudieron escribir.';
  }

  @override
  String get uiTheWriteFinishedButNewchirpAdjusted =>
      'La escritura terminó, pero NewChirp ajustó valores que la radio no admite.';

  @override
  String uiChannelCouldNotBeWritten(Object p0, Object p1, Object p2) {
    return 'El canal $p0 $p1 no se pudo escribir: $p2';
  }

  @override
  String uiNameChangedFromTo(Object p0, Object p1) {
    return 'el nombre cambió de \"$p0\" a \"$p1\"';
  }

  @override
  String uiLockedFieldSEverythingElseWas(Object p0) {
    return 'campos bloqueados: $p0; todo lo demás se escribió';
  }

  @override
  String get uiCancellingSafely => 'Cancelando de forma segura…';

  @override
  String get uiUpdateAvailable => 'Actualización disponible';

  @override
  String uiNewchirpIsReady(Object p0) {
    return 'NewChirp $p0 está listo';
  }

  @override
  String uiNewchirpIsAvailableYouAreRunning(Object p0, Object p1) {
    return 'NewChirp $p0 está disponible. Usted tiene la $p1.\n\nAbra la página de descarga para obtener el instalador adecuado para su equipo.';
  }

  @override
  String uiYouAreRunningNewchirpCanDownload(Object p0, Object p1) {
    return 'Usted tiene la $p0. NewChirp puede descargar e instalar la $p1 por usted y volver a abrirse automáticamente. No hace falta visitar el sitio web.';
  }

  @override
  String get uiPreparingTheUpdateDownload =>
      'Preparando la descarga de la actualización…';

  @override
  String uiDownloadingNewchirp(Object p0) {
    return 'Descargando NewChirp $p0…';
  }

  @override
  String get uiVerifiedStartingTheInstallerAndRestarting =>
      'Verificado. Iniciando el instalador y reiniciando NewChirp…';

  @override
  String get uiNewchirpCouldNotPrepareTheUpdate =>
      'NewChirp no pudo preparar la actualización.';

  @override
  String uiDeleteChannel(Object p0) {
    return '¿Eliminar el canal $p0?';
  }

  @override
  String get uiRepeaterRowsThroughStayInThe =>
      'Las filas de repetidor 15 a 22 se quedan en la radio. Se borra el nombre y se restablece la frecuencia del repetidor GMRS sin cambios.';

  @override
  String get uiThisChannelWillBeRemovedFrom =>
      'Este canal se quitará de la configuración actual.';

  @override
  String uiWillBeRemovedFromTheCurrent(Object p0) {
    return '«$p0» se quitará de la configuración actual.';
  }

  @override
  String uiStoredImageReadyForYouCan(Object p0) {
    return 'Imagen guardada lista para $p0. Puede escribir sin volver a leer.';
  }

  @override
  String get uiARadioImageIsLoadedFrom =>
      'Hay una imagen de radio cargada en esta sesión. Revise todos los cambios antes de escribir.';

  @override
  String get uiClearSearchAndColumnFiltersTo =>
      'Borre la búsqueda y los filtros de columnas para reordenar los canales';

  @override
  String get uiRearrangeChannels => 'Reordenar canales';

  @override
  String get uiPreparingFrequencyReference =>
      'Preparando la referencia de frecuencias…';

  @override
  String get uiPrintingFrequencyReference =>
      'Imprimiendo la referencia de frecuencias…';

  @override
  String get uiTheGmrsFrsReference => 'La referencia GMRS/FRS';

  @override
  String get uiNewchirpChannelList => 'Lista de canales de NewChirp';

  @override
  String uiNewchirpChannelList2(Object p0) {
    return 'Lista de canales de NewChirp: $p0';
  }

  @override
  String get uiPreparingChannelList => 'Preparando la lista de canales…';

  @override
  String get uiChannelList => 'la lista de canales';

  @override
  String get uiPrintingChannelList => 'Imprimiendo la lista de canales…';

  @override
  String get uiTheChannelList => 'La lista de canales';

  @override
  String get uiNoPrintersFound => 'No se encontraron impresoras';

  @override
  String uiNewchirpCouldNotFindAnySystem(Object p0) {
    return 'NewChirp no encontró ninguna impresora del sistema, así que el PDF de $p0 se abrió en su visor de PDF predeterminado. Use el comando Imprimir del visor para imprimirlo.';
  }

  @override
  String uiThePdfWasOpenedInYour(Object p0) {
    return 'El PDF de $p0 se abrió en su visor de PDF predeterminado. Use el comando Imprimir del visor para imprimirlo.';
  }

  @override
  String get uiFrequencyMhz => 'Frecuencia (MHz)';

  @override
  String get uiUseNotes => 'Uso / notas';

  @override
  String get uiSharedMhzInterstitial => 'Intersticial de 462 MHz compartido';

  @override
  String get uiHandheldOnly => 'Solo portátiles';

  @override
  String get uiMainRepeaterOutput => 'Principal / salida de repetidor';

  @override
  String get uiChMhzInterstitial => 'Can. 1-7: intersticial de 462 MHz';

  @override
  String get uiChMhzInterstitial2 => 'Can. 8-14: intersticial de 467 MHz';

  @override
  String get uiChMhzMain => 'Can. 15-22: principal de 462 MHz';

  @override
  String get uiFrsPower => 'Potencia FRS';

  @override
  String get uiGmrsPower => 'Potencia GMRS';

  @override
  String get uiInputYouTransmit => 'Entrada - usted transmite';

  @override
  String get uiOutputYouListen => 'Salida - usted escucha';

  @override
  String get uiInputOutputMhz => 'Entrada = salida + 5 MHz';

  @override
  String get uiPreparingTransfer => 'Preparando la transferencia...';

  @override
  String get uiWaitingForTheRadioToReport =>
      'Esperando a que la radio informe del progreso';

  @override
  String uiCompleteElapsed(Object p0, Object p1) {
    return '$p0 % completado  |  $p1 transcurrido';
  }

  @override
  String get uiEnterAWholeNumber => 'Introduzca un número entero';

  @override
  String uiValueMustBeAtLeast(Object p0) {
    return 'El valor debe ser al menos $p0';
  }

  @override
  String uiValueMustBeAtMost(Object p0) {
    return 'El valor debe ser como máximo $p0';
  }

  @override
  String uiUseAtLeastCharacters(Object p0) {
    return 'Use al menos $p0 caracteres';
  }

  @override
  String uiUseAtMostCharacters(Object p0) {
    return 'Use como máximo $p0 caracteres';
  }

  @override
  String get uiEnterAValidEmailAddress =>
      'Introduzca un correo electrónico válido.';

  @override
  String get uiCouldNotSendTheErrorReport =>
      'No se pudo enviar el informe de error.';

  @override
  String get uiErrorReportSent => 'Informe de error enviado';

  @override
  String get uiSubmitErrorReport => 'Enviar informe de error';

  @override
  String get uiNoDiagnosticEventsRecorded =>
      'No hay eventos de diagnóstico registrados.';

  @override
  String get uiSendReport => 'Enviar informe';

  @override
  String get uiWaitingForMygmrsSignInYou =>
      'Esperando el inicio de sesión en myGMRS. Puede cancelar este intento.';

  @override
  String get uiSignedInToMygmrsForThis =>
      'Sesión iniciada en myGMRS para esta sesión.';

  @override
  String get uiMygmrsSignInCancelled => 'Inicio de sesión en myGMRS cancelado.';

  @override
  String get uiSigningOutOfMygmrs => 'Cerrando la sesión de myGMRS…';

  @override
  String get uiSignedOutOfMygmrs => 'Sesión de myGMRS cerrada.';

  @override
  String get uiEnterBothLatitudeAndLongitudeOr =>
      'Introduzca latitud y longitud, o ninguna de las dos.';

  @override
  String get uiLatitudeMustBeBetweenAnd =>
      'La latitud debe estar entre -90 y 90.';

  @override
  String get uiLongitudeMustBeBetweenAnd =>
      'La longitud debe estar entre -180 y 180.';

  @override
  String get uiUseEitherAZipCodeOr =>
      'Use un código postal o coordenadas, no ambos.';

  @override
  String get uiLatitudeAndLongitudeAreRequiredFor =>
      'La búsqueda por radio requiere latitud y longitud.';

  @override
  String get uiRadiusMustBeGreaterThanZero =>
      'El radio debe ser mayor que cero.';

  @override
  String get uiSignInToMygmrsBeforeSearching =>
      'Inicie sesión en myGMRS antes de buscar.';

  @override
  String get uiSigningInToMygmrs => 'Iniciando sesión en myGMRS…';

  @override
  String get uiSearchingRepeaterbook => 'Buscando en RepeaterBook…';

  @override
  String get uiMygmrsRequiresAnActiveGmrsLicense2 =>
      'myGMRS exige una licencia GMRS activa para mostrar las frecuencias de repetidores. Compruebe que ha iniciado sesión con una cuenta válida. La búsqueda de texto de myGMRS no reconoce nombres de condado; introduzca un código postal de 5 dígitos para buscar repetidores cercanos.';

  @override
  String get uiRepeaterbookMayNotHaveAGmrs =>
      'Puede que RepeaterBook aún no tenga repetidores GMRS de esta zona.';

  @override
  String get uiCoordinatesAreSearchedWithinTheSelected =>
      'Las coordenadas se buscan dentro de la región seleccionada.';

  @override
  String get uiCheckThatCountryAndRegionAre =>
      'Compruebe que el país y la región sean correctos.';

  @override
  String uiNoMatchingGmrsRepeatersWereFound(Object p0, Object p1, Object p2) {
    return 'No se encontraron repetidores GMRS que coincidan$p0. $p1 $p2';
  }

  @override
  String get uiOpenUse => 'uso abierto';

  @override
  String get uiFmAnalog => 'FM analógica';

  @override
  String uiNoMatchingRepeatersWereFoundZip(Object p0, Object p1) {
    return 'No se encontraron repetidores que coincidan$p0. Las búsquedas por código postal usan 50 km por defecto; aumente el radio o desactive los filtros activos.$p1';
  }

  @override
  String uiNoMatchingRepeatersWereFoundCoordinates(Object p0, Object p1) {
    return 'No se encontraron repetidores que coincidan$p0. Las coordenadas se buscan dentro de la región seleccionada. Aumente el radio o desactive los filtros activos.$p1';
  }

  @override
  String uiNoMatchingRepeatersWereFoundCheck(Object p0, Object p1) {
    return 'No se encontraron repetidores que coincidan$p0. Compruebe la región seleccionada o aumente el radio.$p1';
  }

  @override
  String get uiNoTone => 'sin tono';

  @override
  String get uiCancelSignIn => 'Cancelar inicio de sesión';

  @override
  String get uiSignOut => 'Cerrar sesión';

  @override
  String get uiSignInToMygmrs => 'Iniciar sesión en myGMRS';

  @override
  String get uiRepeaterNameCityOrZipCode =>
      'Nombre del repetidor, ciudad o código postal';

  @override
  String get uiCityZipCountyCallsignLandmarkOr =>
      'Ciudad, código postal, condado, indicativo, lugar o notas';

  @override
  String get uiADigitZipSearchesNearbyRepeaters =>
      'Un código postal de 5 dígitos busca repetidores cercanos. myGMRS no admite nombres de condado.';

  @override
  String get uiADigitZipSearchesRepeatersWithin =>
      'Un código postal de 5 dígitos busca repetidores a menos de 50 km por defecto.';

  @override
  String get uiAllCounties => 'Todos los condados';

  @override
  String get uiSearchToPreviewRepeaterChannels =>
      'Busque para ver los canales de repetidores.';

  @override
  String uiShownOfLoadedDataFrom(Object p0, Object p1, Object p2) {
    return '$p0 mostrados de $p1 cargados • Datos de $p2';
  }

  @override
  String get uiAddSelected => 'Añadir seleccionados';

  @override
  String uiAddSelected2(Object p0) {
    return 'Añadir $p0 seleccionados';
  }

  @override
  String get uiEditSelectedProperties => 'Editar propiedades seleccionadas';

  @override
  String uiCopyChannels(Object p0) {
    return 'Copiar $p0 canales';
  }

  @override
  String uiCutChannels(Object p0) {
    return 'Cortar $p0 canales';
  }

  @override
  String uiPasteChannels(Object p0) {
    return 'Pegar $p0 canales';
  }

  @override
  String uiClearSelectedChannels(Object p0) {
    return 'Vaciar $p0 canales seleccionados';
  }

  @override
  String get uiClearChannel => 'Vaciar canal';

  @override
  String get uiEmptyMemorySlotDoubleClickTo =>
      'Posición de memoria vacía. Haga doble clic para crear un canal.';

  @override
  String get uiDoubleClickToEditChannel =>
      'Haga doble clic para editar el canal';

  @override
  String get uiDragToRearrangeChannel => 'Arrastre para reordenar el canal';

  @override
  String get uiEmptySlot => 'Posición vacía';

  @override
  String get uiBugReportSent => 'Informe de error enviado';

  @override
  String get uiSubmitBugReport2 => 'Enviar informe de error';

  @override
  String uiGiveEveryEntryANameBefore(Object p0) {
    return 'Ponga nombre a cada entrada de tipo $p0 antes de guardar.';
  }

  @override
  String get uiAddAChannelToCreate => 'Añada un canal para crearla';

  @override
  String get uiAChannelMayBelongToMore =>
      'Un canal puede pertenecer a más de una entrada.';

  @override
  String get uiAChannelCanBelongToOne =>
      'Un canal solo puede pertenecer a una entrada.';

  @override
  String get uiThisEmptyEntryIsTheRadio =>
      'Esta entrada vacía es el banco o la zona libre de la radio. Añada un canal para crearla.';

  @override
  String uiChannelsSelected(Object p0) {
    return '$p0 canales seleccionados';
  }

  @override
  String get glossFrs =>
      'Family Radio Service. Servicio UHF de EE. UU. que no requiere licencia.';

  @override
  String get glossGmrs =>
      'General Mobile Radio Service. Servicio UHF de EE. UU. que requiere licencia.';

  @override
  String get glossRx =>
      'Recepción. La frecuencia o el tono que se usa al escuchar.';

  @override
  String get glossTx =>
      'Transmisión. La frecuencia o el tono que se usa al transmitir.';

  @override
  String get glossCtcss =>
      'Continuous Tone-Coded Squelch System. Un tono analógico subaudible, conocido como tono PL.';

  @override
  String get glossTsql =>
      'Silenciador por tono. Exige el mismo tono CTCSS para recibir y transmitir.';

  @override
  String get glossDcs =>
      'Digital-Coded Squelch System. Un código de silenciador digital; NewChirp lo llama DTCS.';

  @override
  String get glossDtcs =>
      'Digital-Coded Squelch System. Un código digital que se usa como un tono CTCSS para abrir un receptor o repetidor.';

  @override
  String get glossDtcsPol =>
      'Polaridad DTCS. La polaridad normal o invertida debe coincidir entre la radio y el repetidor.';

  @override
  String get glossFm =>
      'Modulación de frecuencia. Modo de voz analógico estándar.';

  @override
  String get glossNfm =>
      'FM de banda estrecha. Ocupa menos ancho de banda y es habitual en FRS, GMRS y redes de repetidores con mucho tráfico.';

  @override
  String get glossAm =>
      'Modulación de amplitud. La usan algunos canales aeronáuticos y de radioaficionado.';

  @override
  String get glossDuplex =>
      'Relación entre transmisión y recepción. Símplex usa la misma frecuencia; los desplazamientos y el modo split usan otra frecuencia de transmisión.';

  @override
  String get glossOffset =>
      'La diferencia de frecuencia entre recepción y transmisión.';

  @override
  String get glossSplit =>
      'Frecuencias de recepción y transmisión independientes, en lugar de un desplazamiento fijo.';

  @override
  String get glossStep =>
      'Tamaño del paso de sintonía al cambiar de frecuencia.';

  @override
  String get glossScan =>
      'Si el canal se incluye en el escaneo o se marca para omitirlo.';

  @override
  String get glossBcl =>
      'Busy Channel Lockout. Impide transmitir cuando el canal ya está en uso.';

  @override
  String get glossPttId =>
      'Identificación de la estación que se envía al principio o al final de una transmisión, según la radio.';

  @override
  String get glossSCode =>
      'Selector de código de señalización. Elige qué código PTT-ID o de señalización guardado usa el canal.';

  @override
  String get fileSaveWarning =>
      'Guardar este archivo no escribe estos cambios en su radio. Debe escribir los cambios en la radio para que surtan efecto.';

  @override
  String repeaterRangeIn(String location) {
    return ' en $location';
  }

  @override
  String repeaterRangeZip(String km, String zip, String location) {
    return ' a menos de $km km del código postal $zip en $location';
  }

  @override
  String repeaterRangeCoords(String km, String location) {
    return ' a menos de $km km de sus coordenadas en $location';
  }

  @override
  String repeaterFilterHint(String filters) {
    return ' Los filtros activos exigen $filters; pruebe a desactivarlos.';
  }

  @override
  String get listAnd => ' y ';

  @override
  String occupiedBody(String occupant, Object channel, String moving) {
    return '$occupant ya usa el canal $channel. Elija cómo colocar $moving.';
  }

  @override
  String get anExistingChannel => 'Un canal existente';

  @override
  String get thisChannel => 'este canal';

  @override
  String channelsNeedAttention(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count canales requieren atención antes de escribir.',
      one: '1 canal requiere atención antes de escribir.',
    );
    return '$_temp0';
  }

  @override
  String moreValidationIssues(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count problemas de validación más.',
      one: '1 problema de validación más.',
    );
    return '$_temp0';
  }

  @override
  String repeatersNoneImportable(int count, String source) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other:
          '$source devolvió $count repetidores que coinciden, pero no se pudo importar ninguno.',
      one:
          '$source devolvió 1 repetidor que coincide, pero no se pudo importar ninguno.',
    );
    return '$_temp0';
  }

  @override
  String countyCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count condados',
      one: '1 condado',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesButton(int count, int limit) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'Acortar $count nombres a $limit',
      one: 'Acortar 1 nombre a $limit',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesTitle(int limit) {
    return '¿Acortar los nombres a $limit caracteres?';
  }

  @override
  String shortenNamesBody(int count, int limit) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other:
          '$count nombres de canal son más largos de lo que permite la radio. NewChirp conservará los primeros $limit caracteres de cada uno.',
      one:
          '1 nombre de canal es más largo de lo que permite la radio. NewChirp conservará sus primeros $limit caracteres.',
    );
    return '$_temp0 Puede deshacerlo.';
  }

  @override
  String shortenNamesMore(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'y $count más',
      one: 'y 1 más',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesDuplicates(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other:
          '$count nombres acortados coincidirán con los de otros canales. Revíselos antes de escribir.',
      one:
          '1 nombre acortado coincidirá con el de otro canal. Revíselo antes de escribir.',
    );
    return '$_temp0';
  }

  @override
  String shortenNamesAction(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'Acortar $count nombres',
      one: 'Acortar 1 nombre',
    );
    return '$_temp0';
  }
}
