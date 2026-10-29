import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/local_file_opener.dart';

void main() {
  test('uses the Windows file protocol handler for local files', () {
    const path = r'C:\Users\Test User\AppData\Local\Temp\reference.pdf';

    final command = localFileOpenCommand(LocalFilePlatform.windows, path);

    expect(command.executable, r'C:\Windows\System32\rundll32.exe');
    expect(command.arguments, ['url.dll,FileProtocolHandler', path]);
  });

  test('uses open on macOS and xdg-open on Linux', () {
    final mac = localFileOpenCommand(
      LocalFilePlatform.macos,
      '/tmp/reference.pdf',
    );
    final linux = localFileOpenCommand(
      LocalFilePlatform.linux,
      '/tmp/reference.pdf',
    );

    expect(mac.executable, '/usr/bin/open');
    expect(mac.arguments, ['/tmp/reference.pdf']);
    expect(linux.executable, 'xdg-open');
    expect(linux.arguments, ['/tmp/reference.pdf']);
  });
}
