import 'dart:io';

class RadioImageStore {
  RadioImageStore({Directory? rootDirectory}) : _rootDirectory = rootDirectory;

  final Directory? _rootDirectory;

  /// Copies a radio image into the app's image folder as the model's latest image; returns the new path.
  Future<String> saveForModel(String model, String sourcePath) async {
    final destination = File(pathForModel(model));
    await destination.parent.create(recursive: true);
    await File(sourcePath).copy(destination.path);
    return destination.path;
  }

  /// Copies a radio image for one open document (tab) of [model]; returns the new path.
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

  /// Where the model's latest image is kept. Characters unsafe in file names become "_".
  String pathForModel(String model) {
    final safeModel = model.replaceAll(RegExp(r'[^A-Za-z0-9_.-]'), '_');
    return '${_imageDirectory().path}/$safeModel.img';
  }

  /// Where one document's image is kept (model name plus document number).
  String pathForDocument(String model, int documentId) {
    final safeModel = model.replaceAll(RegExp(r'[^A-Za-z0-9_.-]'), '_');
    return '${_imageDirectory().path}/$safeModel-document-$documentId.img';
  }

  /// The images folder: the test override, or the per-user app data folder.
  Directory _imageDirectory() {
    if (_rootDirectory != null) return _rootDirectory;
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return Directory('$home/Library/Application Support/NewChirp/images');
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
