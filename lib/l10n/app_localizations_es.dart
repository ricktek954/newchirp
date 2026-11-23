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
}
