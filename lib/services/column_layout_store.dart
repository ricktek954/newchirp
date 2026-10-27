import 'dart:convert';
import 'dart:io';

class ColumnLayout {
  const ColumnLayout({
    required this.order,
    required this.widths,
    this.showEmptySlots = false,
  });

  final List<String> order;
  final Map<String, double> widths;
  final bool showEmptySlots;
}

class ColumnLayoutStore {
  ColumnLayoutStore({String? path}) : _path = path ?? _defaultPath();

  final String _path;

  Future<ColumnLayout?> load() async {
    final file = File(_path);
    if (!await file.exists()) return null;
    try {
      final data = jsonDecode(await file.readAsString()) as Map;
      final order = (data['order'] as List? ?? const [])
          .map((item) => item.toString())
          .toList();
      final widths = <String, double>{};
      for (final entry in (data['widths'] as Map? ?? const {}).entries) {
        final width = (entry.value as num?)?.toDouble();
        if (width != null && width.isFinite && width >= 48 && width <= 480) {
          widths[entry.key.toString()] = width;
        }
      }
      return ColumnLayout(
        order: order,
        widths: widths,
        showEmptySlots: data['showEmptySlots'] == true,
      );
    } on FormatException {
      return null;
    } on FileSystemException {
      return null;
    }
  }

  Future<void> save(ColumnLayout layout) async {
    final file = File(_path);
    await file.parent.create(recursive: true);
    await file.writeAsString(
      jsonEncode({
        'version': 2,
        'order': layout.order,
        'widths': layout.widths,
        'showEmptySlots': layout.showEmptySlots,
      }),
      flush: true,
    );
  }

  static String _defaultPath() {
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return '$home/Library/Application Support/NewChirp/column-layout.json';
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return '$appData\\NewChirp\\column-layout.json';
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return '$config/newchirp/column-layout.json';
  }
}
