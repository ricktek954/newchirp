import 'package:flutter/material.dart';

import '../models/marine_channels.dart';

class MarineTemplateDialog extends StatefulWidget {
  const MarineTemplateDialog({super.key, this.initialPlan});

  final MarineChannelPlan? initialPlan;

  @override
  State<MarineTemplateDialog> createState() => _MarineTemplateDialogState();
}

class _MarineTemplateDialogState extends State<MarineTemplateDialog> {
  late MarineChannelPlan _plan =
      widget.initialPlan ?? MarineChannelPlan.unitedStates;
  bool _programTransmit = false;

  @override
  Widget build(BuildContext context) {
    final definitions = marineChannelDefinitionsFor(_plan);
    final receiveOnly = definitions
        .where((channel) => channel.receiveOnly)
        .length;
    final transmitCapable = definitions.length - receiveOnly;
    return AlertDialog(
      title: const Text('Marine VHF channel template'),
      content: SizedBox(
        width: 640,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<MarineChannelPlan>(
                key: const ValueKey('marine-plan-selector'),
                initialValue: _plan,
                decoration: const InputDecoration(labelText: 'Plan'),
                items: [
                  for (final plan in MarineChannelPlan.values)
                    DropdownMenuItem(value: plan, child: Text(plan.label)),
                ],
                onChanged: (plan) {
                  if (plan != null) setState(() => _plan = plan);
                },
              ),
              const SizedBox(height: 10),
              Text(
                _plan.description,
                style: const TextStyle(color: Colors.black54),
              ),
              const SizedBox(height: 6),
              Text(
                'Source: ${_plan.source}',
                style: const TextStyle(color: Colors.black45, fontSize: 12),
              ),
              const SizedBox(height: 14),
              DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xFFEAF4EF),
                  borderRadius: BorderRadius.circular(9),
                  border: Border.all(color: const Color(0xFFB9D8C8)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline, color: Color(0xFF1F7455)),
                      const SizedBox(width: 9),
                      const Expanded(
                        child: Text(
                          'The channel plan is selected by regulatory region, '
                          'not ZIP code. Marine channel assignments are '
                          'national or international and do not change by '
                          'postal code.',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
              CheckboxListTile(
                key: const ValueKey('marine-program-transmit'),
                contentPadding: EdgeInsets.zero,
                value: _programTransmit,
                onChanged: (value) =>
                    setState(() => _programTransmit = value == true),
                title: const Text('Program ship transmit frequencies'),
                subtitle: const Text(
                  'Receive-only is the safe default. Enable this only when '
                  'the radio and installation are authorized for marine VHF '
                  'transmission.',
                ),
              ),
              if (_programTransmit) ...[
                const SizedBox(height: 8),
                DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF3E7),
                    borderRadius: BorderRadius.circular(9),
                    border: Border.all(color: const Color(0xFFE7C9A5)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.warning_amber_rounded,
                          color: Color(0xFF9B5B18),
                        ),
                        const SizedBox(width: 9),
                        const Expanded(
                          child: Text(
                            'Most amateur transceivers are not type-accepted '
                            'for marine-band transmit. Prohibited and '
                            'receive-only channels remain transmission-disabled.',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 14),
              Text(
                '${definitions.length} channels: '
                '$transmitCapable transmit-capable, $receiveOnly receive-only.',
                key: const ValueKey('marine-template-summary'),
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              if (!_programTransmit)
                const Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text(
                    'All rows will be added with transmit disabled.',
                    style: TextStyle(color: Colors.black54, fontSize: 12),
                  ),
                ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          key: const ValueKey('marine-template-continue'),
          onPressed: () => Navigator.pop(
            context,
            MarineTemplateSelection(
              plan: _plan,
              programTransmit: _programTransmit,
            ),
          ),
          child: const Text('Continue'),
        ),
      ],
    );
  }
}
