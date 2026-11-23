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
}
