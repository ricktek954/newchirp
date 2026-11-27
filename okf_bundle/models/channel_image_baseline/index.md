# channel_image_baseline

## Classs

- [ChannelImageBaseline](ChannelImageBaseline.md) — Fingerprint of the channel list last read from, imported from, or written
- [ChannelLibrarySnapshot](ChannelLibrarySnapshot.md) — Channel counts and the radio-image match for one library refresh.
- [ChannelLibraryStatsCache](ChannelLibraryStatsCache.md) — Remembers the last library snapshot so search and row selection can skip it.

## Functions

- [channelImageMatch](channelImageMatch.md) — How the on-screen channel list relates to the stored radio image: no image,
- [channelImageStatusText](channelImageStatusText.md) — Status-bar sentence explaining [match] to the user.
- [channelLibrarySnapshot](channelLibrarySnapshot.md) — Counts channels and compares with the radio image for one library refresh.
- [channelLibraryWriteReady](channelLibraryWriteReady.md) — True when Write may be enabled: not busy, no invalid channels, a port,
- [channelListSignature](channelListSignature.md) — Fingerprint (JSON text) of a channel list plus its cleared slots, sorted by
- [clearedLocationsAfterReplacement](clearedLocationsAfterReplacement.md) — Cleared slots to retain when replacing the current channel library.
- [clearedLocationsForUpload](clearedLocationsForUpload.md) — All radio locations that must be blank for the current library to match.
- [markDirty](markDirty.md) — Forces the next [read] to recompute (after editing a channel in place).
- [read](read.md) — The cached snapshot, recomputed only when an input changed or [markDirty] was called.
