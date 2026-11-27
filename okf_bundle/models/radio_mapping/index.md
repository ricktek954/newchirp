# radio_mapping

## Classs

- [RadioMappingEntry](RadioMappingEntry.md)
- [RadioMappingModel](RadioMappingModel.md)

## Functions

- [_remapLocations](remapLocations.md) — Applies [locations] to a list of channel numbers, dropping deleted ones and duplicates.
- [copyWith](copyWith.md) — Copy with a new list of mappings (zones/banks).
- [mappingRangeAt](mappingRangeAt.md)
- [radioMappingsFromJson](radioMappingsFromJson.md) — Parses the bridge's mapping list, skipping entries that aren't objects.
- [radioMappingsSignature](radioMappingsSignature.md) — Fixed (non-editable) zone models are derived from channel numbers by the
- [radioMappingsToJson](radioMappingsToJson.md) — Mapping models as JSON for the bridge.
- [remapRadioMappingLocations](remapRadioMappingLocations.md) — Updates zone/bank membership after channels move. [locations] maps old ->
- [retainingChannels](retainingChannels.md) — Copy that keeps only channels still present in [activeLocations].
- [toJson](toJson.md) — Serialized form sent to and from the Python bridge.
