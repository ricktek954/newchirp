# radio_channel

## Functions

- [_frequencyFitsStep](frequencyFitsStep.md)
- [_isPlusFiveMhz](isPlusFiveMhz.md)
- [_isZeroMhz](isZeroMhz.md)
- [_midlandGmrsChannel](midlandGmrsChannel.md) — Midland channel 1-22 for a memory slot. Slots 31-107 are not fixed.
- [_nearestFrequencyForSteps](nearestFrequencyForSteps.md)
- [ChannelExtraField](ChannelExtraField.md)
- [channelNumberLabel](channelNumberLabel.md) — Channel number shown in the list.
- [clear](clear.md)
- [copy](copy.md)
- [gmrsChannelForHz](gmrsChannelForHz.md) — GMRS channel 1-22 for a receive frequency, or null when it is not one.
- [gmrsChannelMenuLabel](gmrsChannelMenuLabel.md) — Menu line for the receive-channel dropdown.
- [gmrsStandardRxHz](gmrsStandardRxHz.md) — Official receive frequency in Hz for one of the 22 GMRS channels.
- [gmrsStarterChannels](gmrsStarterChannels.md)
- [isGmrsRepeaterOutputMhz](isGmrsRepeaterOutputMhz.md) — GMRS repeater outputs from 462.550 through 462.725 MHz.
- [isMidlandRepeaterRow](isMidlandRepeaterRow.md) — Whether [location] is one of the eight repeater rows on this radio.
- [mhzLabelFromHz](mhzLabelFromHz.md)
- [midlandCanSelectOffset](midlandCanSelectOffset.md) — Offset can be chosen only for GMRS channels 15 through 22.
- [midlandDuplexChoices](midlandDuplexChoices.md) — Duplex choices for one MXT295 slot.
- [midlandDuplexIsLocked](midlandDuplexIsLocked.md) — Channels 1-14, a GMRS 1-14 receive channel, and the repeater rows
- [midlandFixedRxHz](midlandFixedRxHz.md) — Official receive frequency in Hz for MXT295 channels 1 through 22.
- [midlandGmrsIssues](midlandGmrsIssues.md) — Why this MXT295 channel is not legal. Empty for every other radio.
- [midlandReceiveChannelChoices](midlandReceiveChannelChoices.md) — Dropdown rows for Receive channel. Fixed rows have one choice.
- [midlandReceiveChannelIsLocked](midlandReceiveChannelIsLocked.md) — Channels 1 through 22 already have a receive channel, so the list
- [midlandReceiveChannelIsUnset](midlandReceiveChannelIsUnset.md) — A new row has no receive channel yet. 146.52 MHz is the old placeholder.
- [midlandReceiveChannelValue](midlandReceiveChannelValue.md) — Selected value for [midlandReceiveChannelChoices].
- [midlandReceiveGmrsChannel](midlandReceiveGmrsChannel.md) — GMRS channel shown for this row. Fixed rows use the slot. Other rows
- [nextAvailableLocation](nextAvailableLocation.md)
- [prepareMxt295Editor](prepareMxt295Editor.md) — Snaps locked MXT295 fields to the legal GMRS values.
- [RadioChannel](RadioChannel.md)
- [restorePlainMidlandRepeater](restorePlainMidlandRepeater.md) — Puts the standard GMRS repeater back in this row and clears the name.
- [scanChoices](scanChoices.md) — Edit-screen choices for the scan codes this radio allows.
- [scanLabel](scanLabel.md) — Word shown for a stored scan code. Unknown codes stay visible.
- [showsMidlandChannelNumbers](showsMidlandChannelNumbers.md) — This radio's list uses Midland's channel numbers instead of raw slots.
- [toJson](toJson.md)
- [useGmrsReceiveChannel](useGmrsReceiveChannel.md) — Sets this row to one of the 22 GMRS receive channels.
- [validate](validate.md)
