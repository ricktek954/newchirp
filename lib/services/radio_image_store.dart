import 'dart:io';

class RadioImageStore {
  RadioImageStore({Directory? rootDirectory})
    : _rootDirectory = rootDirectory;

  final Directory? _rootDirectory;

  Future<String> saveForModel(String model, String sourcePath) async {
    final destination = File(pathForModel(model));
    await destination.parent.create(recursive: true);
    await File(sourcePath).copy(destination.path);
    return destination.path;
  }

  Future<String> saveForDocument(
    String model,
    String sourcePath,
    int documentId,
  ) async {
    final destination = File(pathForDocument(model, documentId));
    await destination.parent.create(recursive: true);
    await File(sourcePath).copy(destination.path);
    return destination.path;
  }

  bool hasForModel(String model) => File(pathForModel(model)).existsSync();

  String pathForModel(String model) {
    final safeModel = model.replaceAll(RegExp(r'[^A-Za-z0-9_.-]'), '_');
    return '${_imageDirectory().path}/$safeModel.img';
  }

  String pathForDocument(String model, int documentId) {
    final safeModel = model.replaceAll(RegExp(r'[^A-Za-z0-9_.-]'), '_');
    return '${_imageDirectory().path}/$safeModel-tab-$documentId.img';
  }

  Directory _imageDirectory() {
    if (_rootDirectory != null) return _rootDirectory;
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return Directory(
        '$home/Library/Application Support/NewChirp/images',
      );
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return Directory('$appData\\NewChirp\\images');
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return Directory('$config/newchirp/images');
  }
}
