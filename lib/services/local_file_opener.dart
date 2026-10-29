import 'dart:io';

enum LocalFilePlatform { windows, macos, linux }

({String executable, List<String> arguments}) localFileOpenCommand(
  LocalFilePlatform platform,
  String path,
) {
  return switch (platform) {
    LocalFilePlatform.windows => (
      executable: r'C:\Windows\System32\rundll32.exe',
      arguments: ['url.dll,FileProtocolHandler', path],
    ),
    LocalFilePlatform.macos => (executable: '/usr/bin/open', arguments: [path]),
    LocalFilePlatform.linux => (executable: 'xdg-open', arguments: [path]),
  };
}

Future<void> openLocalFile(String path) async {
  final platform = Platform.isWindows
      ? LocalFilePlatform.windows
      : Platform.isMacOS
      ? LocalFilePlatform.macos
      : LocalFilePlatform.linux;
  final command = localFileOpenCommand(platform, path);
  final result = await Process.run(command.executable, command.arguments);
  if (result.exitCode != 0) {
    final error = result.stderr.toString().trim();
    throw ProcessException(
      command.executable,
      command.arguments,
      error.isEmpty ? 'Could not open the file.' : error,
      result.exitCode,
    );
  }
}
