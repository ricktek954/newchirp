import '../l10n/l10n.dart';
import 'package:flutter/material.dart';

import '../services/diagnostic_log.dart';

class ErrorReportDialog extends StatefulWidget {
  const ErrorReportDialog({
    super.key,
    required this.diagnosticLog,
    required this.summary,
    required this.technical,
    required this.radio,
    required this.firmware,
    required this.version,
    required this.cable,
  });

  final DiagnosticLog diagnosticLog;
  final String summary;
  final String? technical;
  final String radio;
  final String firmware;
  final String version;
  final String cable;

  @override
  State<ErrorReportDialog> createState() => _ErrorReportDialogState();
}

class _ErrorReportDialogState extends State<ErrorReportDialog> {
  final _emailController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _sending = false;
  bool _sent = false;
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    if (!email.contains('@') || email.startsWith('@') || email.endsWith('@')) {
      setState(() => _error = context.l10n.uiEnterAValidEmailAddress);
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    final notes = _descriptionController.text.trim();
    final description = [
      'Reported error: ${widget.summary}',
      if (widget.technical != null && widget.technical!.trim().isNotEmpty)
        'Technical details:\n${widget.technical}',
      if (notes.isNotEmpty) 'Reporter notes:\n$notes',
    ].join('\n\n');
    try {
      await widget.diagnosticLog.submit(
        email: email,
        description: description,
        radio: widget.radio,
        firmware: widget.firmware,
        version: widget.version,
        cable: widget.cable,
      );
      widget.diagnosticLog.record(
        'report',
        'Error report submitted',
        context: {
          'radio': widget.radio,
          'firmware': widget.firmware,
          'version': widget.version,
        },
      );
      if (mounted) setState(() => _sent = true);
    } on DiagnosticReportException catch (error) {
      widget.diagnosticLog.record(
        'report',
        'Error report submission failed: $error',
      );
      if (mounted) setState(() => _error = error.message);
    } on Object {
      if (mounted) {
        setState(() => _error = context.l10n.uiCouldNotSendTheErrorReport);
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final diagnosticPreview = widget.diagnosticLog.buildReport(
      maxCharacters: 6000,
    );
    return AlertDialog(
      title: Text(
        _sent ? context.l10n.uiBugReportSent : context.l10n.uiSubmitBugReport2,
      ),
      content: SizedBox(
        width: 620,
        child: SingleChildScrollView(
          child: _sent
              ? Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.check_circle_outline,
                        color: Color(0xFF1F7455),
                        size: 44,
                      ),
                      SizedBox(height: 14),
                      Text(
                        context.l10n.uiThanksTheDiagnosticLogAndProblem,
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                )
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      widget.summary,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      autocorrect: false,
                      decoration: InputDecoration(
                        labelText: context.l10n.uiYourEmail,
                        helperText: context.l10n.uiUsedOnlyIfTheDeveloperNeeds,
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _descriptionController,
                      minLines: 3,
                      maxLines: 6,
                      maxLength: 3500,
                      decoration: InputDecoration(
                        labelText: context.l10n.uiWhatWereYouTryingToDo,
                        alignLabelWithHint: true,
                      ),
                    ),
                    Text(
                      context.l10n.uiTheReportIncludesAppAndOperating2,
                      style: TextStyle(color: Colors.black54, height: 1.4),
                    ),
                    const SizedBox(height: 8),
                    ExpansionTile(
                      tilePadding: EdgeInsets.zero,
                      title: Text(
                        context.l10n.uiPreviewDiagnosticEvents(
                          widget.diagnosticLog.entryCount,
                        ),
                        style: const TextStyle(fontSize: 13),
                      ),
                      childrenPadding: const EdgeInsets.only(bottom: 8),
                      children: [
                        Container(
                          width: double.infinity,
                          constraints: const BoxConstraints(maxHeight: 220),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF3F5F4),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: SingleChildScrollView(
                            child: SelectableText(
                              diagnosticPreview.isEmpty
                                  ? context.l10n.uiNoDiagnosticEventsRecorded
                                  : diagnosticPreview,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 10.5,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 10),
                      Text(
                        _error!,
                        style: const TextStyle(color: Color(0xFF9B3D34)),
                      ),
                    ],
                  ],
                ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _sending ? null : () => Navigator.pop(context),
          child: Text(_sent ? 'Close' : 'Cancel'),
        ),
        if (!_sent)
          FilledButton.icon(
            onPressed: _sending ? null : _submit,
            icon: _sending
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send_outlined),
            label: Text(_sending ? 'Sending…' : context.l10n.uiSendReport),
          ),
      ],
    );
  }
}
