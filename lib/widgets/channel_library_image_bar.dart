import 'package:flutter/material.dart';

import '../models/channel_image_baseline.dart';

/// Bottom bar on the Channel Library, matching the Radio settings image bar.
class ChannelLibraryImageBar extends StatelessWidget {
  const ChannelLibraryImageBar({
    super.key,
    required this.match,
    required this.canDiscard,
    required this.canWrite,
    required this.showConnect,
    required this.onDiscard,
    required this.onWrite,
    required this.onConnect,
  });

  final ChannelImageMatch match;
  final bool canDiscard;
  final bool canWrite;
  final bool showConnect;
  final VoidCallback onDiscard;
  final VoidCallback onWrite;
  final VoidCallback onConnect;

  @override
  Widget build(BuildContext context) {
    final differs = match == ChannelImageMatch.differs;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Text(
                channelImageStatusText(match),
                key: const Key('channel-library-image-status'),
                style: TextStyle(
                  color: differs ? const Color(0xFFC46A15) : Colors.black54,
                  fontWeight: differs ? FontWeight.w700 : FontWeight.w400,
                ),
              ),
            ),
            TextButton(
              key: const Key('channel-library-discard'),
              onPressed: canDiscard ? onDiscard : null,
              child: const Text('Discard changes'),
            ),
            const SizedBox(width: 10),
            if (showConnect)
              OutlinedButton.icon(
                key: const Key('channel-library-connect'),
                onPressed: onConnect,
                icon: const Icon(Icons.cable),
                label: const Text('Connect radio to write'),
              )
            else
              FilledButton.icon(
                key: const Key('channel-library-write'),
                onPressed: canWrite ? onWrite : null,
                icon: const Icon(Icons.save_outlined),
                label: const Text('Write settings to radio'),
              ),
          ],
        ),
      ),
    );
  }
}
