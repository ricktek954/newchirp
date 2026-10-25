import 'package:flutter/material.dart';

/// Warning shown before a Channel Library file save.
///
/// Pops `null` for Cancel, `false` when OK should keep showing the warning,
/// and `true` when OK should hide it next time.
class FileSaveWarningDialog extends StatefulWidget {
  const FileSaveWarningDialog({super.key});

  static const message =
      'Saving this file does not write these changes to your radio. '
      'You must write your changes to the radio for them to take effect.';

  @override
  State<FileSaveWarningDialog> createState() => _FileSaveWarningDialogState();
}

class _FileSaveWarningDialogState extends State<FileSaveWarningDialog> {
  bool _hide = false;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      icon: const Icon(
        Icons.warning_amber_rounded,
        color: Color(0xFFC46A15),
        size: 32,
      ),
      title: const Text('Save file'),
      content: SizedBox(
        width: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(FileSaveWarningDialog.message),
            const SizedBox(height: 8),
            CheckboxListTile(
              value: _hide,
              onChanged: (value) => setState(() => _hide = value ?? false),
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              title: const Text('Do not show me this message again'),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, _hide),
          child: const Text('OK'),
        ),
      ],
    );
  }
}
