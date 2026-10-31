import 'dart:convert';

class RadioMappingEntry {
  const RadioMappingEntry({
    required this.index,
    required this.name,
    required this.channelLocations,
    required this.nameEditable,
  });

  final String index;
  final String name;
  final List<int> channelLocations;
  final bool nameEditable;

  factory RadioMappingEntry.fromJson(Map<String, dynamic> json) =>
      RadioMappingEntry(
        index: '${json['index'] ?? ''}',
        name: '${json['name'] ?? ''}',
        channelLocations: (json['channelLocations'] as List? ?? const [])
            .map((value) => (value as num).toInt())
            .toList(),
        nameEditable: json['nameEditable'] as bool? ?? false,
      );

  RadioMappingEntry copyWith({String? name, List<int>? channelLocations}) =>
      RadioMappingEntry(
        index: index,
        name: name ?? this.name,
        channelLocations: List.of(channelLocations ?? this.channelLocations),
        nameEditable: nameEditable,
      );

  Map<String, Object?> toJson() => {
    'index': index,
    'name': name,
    'channelLocations': channelLocations,
    'nameEditable': nameEditable,
  };
}

class RadioMappingModel {
  const RadioMappingModel({
    required this.index,
    required this.name,
    required this.editable,
    required this.multiple,
    required this.mappings,
  });

  final int index;
  final String name;
  final bool editable;
  final bool multiple;
  final List<RadioMappingEntry> mappings;

  factory RadioMappingModel.fromJson(Map<String, dynamic> json) =>
      RadioMappingModel(
        index: (json['index'] as num?)?.toInt() ?? 0,
        name: '${json['name'] ?? 'Banks'}',
        editable: json['editable'] as bool? ?? false,
        multiple: json['multiple'] as bool? ?? false,
        mappings: (json['mappings'] as List? ?? const [])
            .map(
              (entry) => RadioMappingEntry.fromJson(
                (entry as Map).cast<String, dynamic>(),
              ),
            )
            .toList(),
      );

  RadioMappingModel copyWith({List<RadioMappingEntry>? mappings}) =>
      RadioMappingModel(
        index: index,
        name: name,
        editable: editable,
        multiple: multiple,
        mappings: List.of(mappings ?? this.mappings),
      );

  RadioMappingModel retainingChannels(Set<int> activeLocations) => copyWith(
    mappings: [
      for (final mapping in mappings)
        mapping.copyWith(
          channelLocations: mapping.channelLocations
              .where(activeLocations.contains)
              .toList(),
        ),
    ],
  );

  Map<String, Object?> toJson() => {
    'index': index,
    'name': name,
    'editable': editable,
    'multiple': multiple,
    'mappings': mappings.map((mapping) => mapping.toJson()).toList(),
  };
}

List<RadioMappingModel> radioMappingsFromJson(List<dynamic> values) => values
    .whereType<Map>()
    .map((entry) => RadioMappingModel.fromJson(entry.cast<String, dynamic>()))
    .toList();

List<Map<String, Object?>> radioMappingsToJson(
  Iterable<RadioMappingModel> models,
) => models.map((model) => model.toJson()).toList();

String radioMappingsSignature(Iterable<RadioMappingModel> models) =>
    jsonEncode(radioMappingsToJson(models));

List<RadioMappingModel> remapRadioMappingLocations(
  Iterable<RadioMappingModel> models,
  Map<int, int?> locations,
) {
  return models
      .map(
        (model) => model.copyWith(
          mappings: [
            for (final mapping in model.mappings)
              mapping.copyWith(
                channelLocations: _remapLocations(
                  mapping.channelLocations,
                  locations,
                ),
              ),
          ],
        ),
      )
      .toList();
}

List<int> _remapLocations(Iterable<int> source, Map<int, int?> locations) {
  final seen = <int>{};
  final remapped = <int>[];
  for (final location in source) {
    final next = locations.containsKey(location)
        ? locations[location]
        : location;
    if (next != null && seen.add(next)) remapped.add(next);
  }
  return remapped;
}
