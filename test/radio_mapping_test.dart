import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/radio_mapping.dart';

void main() {
  test('parses editable DM-32UV zone metadata', () {
    final models = radioMappingsFromJson([
      {
        'index': 0,
        'name': 'Zones',
        'editable': true,
        'multiple': true,
        'mappings': [
          {
            'index': '1',
            'name': 'Analog',
            'channelLocations': [1, 2, 3],
            'nameEditable': true,
          },
          {
            'index': '2',
            'name': 'New zone',
            'channelLocations': <int>[],
            'nameEditable': true,
          },
        ],
      },
    ]);

    expect(models, hasLength(1));
    expect(models.single.name, 'Zones');
    expect(models.single.editable, isTrue);
    expect(models.single.multiple, isTrue);
    expect(models.single.mappings[0].channelLocations, [1, 2, 3]);
    expect(models.single.mappings[1].name, 'New zone');
  });

  test('removes memberships for channels no longer in the library', () {
    const model = RadioMappingModel(
      index: 0,
      name: 'Zones',
      editable: true,
      multiple: true,
      mappings: [
        RadioMappingEntry(
          index: '1',
          name: 'Local',
          channelLocations: [1, 3, 7],
          nameEditable: true,
        ),
      ],
    );

    final pruned = model.retainingChannels({1, 7});

    expect(pruned.mappings.single.channelLocations, [1, 7]);
    expect(model.mappings.single.channelLocations, [1, 3, 7]);
  });

  test('signature changes when a zone name or membership changes', () {
    const original = RadioMappingModel(
      index: 0,
      name: 'Zones',
      editable: true,
      multiple: true,
      mappings: [
        RadioMappingEntry(
          index: '1',
          name: 'Local',
          channelLocations: [1],
          nameEditable: true,
        ),
      ],
    );
    final renamed = original.copyWith(
      mappings: [
        original.mappings.single.copyWith(
          name: 'Home',
          channelLocations: [1, 2],
        ),
      ],
    );

    expect(
      radioMappingsSignature([renamed]),
      isNot(radioMappingsSignature([original])),
    );
  });

  test('remaps zone membership when channel locations move', () {
    const model = RadioMappingModel(
      index: 0,
      name: 'Zones',
      editable: true,
      multiple: true,
      mappings: [
        RadioMappingEntry(
          index: '1',
          name: 'Local',
          channelLocations: [1, 3, 7],
          nameEditable: true,
        ),
      ],
    );

    final remapped = remapRadioMappingLocations(
      [model],
      {1: 2, 2: 3, 3: 4, 7: null},
    );

    expect(remapped.single.mappings.single.channelLocations, [2, 4]);
  });

  test('finds the narrowest contiguous bank range for insertion', () {
    const models = [
      RadioMappingModel(
        index: 0,
        name: 'Banks',
        editable: true,
        multiple: false,
        mappings: [
          RadioMappingEntry(
            index: '1',
            name: 'Bank 1',
            channelLocations: [1, 2, 3, 4],
            nameEditable: true,
          ),
          RadioMappingEntry(
            index: '2',
            name: 'Bank 2',
            channelLocations: [5, 6, 7, 8],
            nameEditable: true,
          ),
        ],
      ),
      RadioMappingModel(
        index: 1,
        name: 'Zones',
        editable: true,
        multiple: true,
        mappings: [
          RadioMappingEntry(
            index: 'A',
            name: 'Across banks',
            channelLocations: [1, 5, 6],
            nameEditable: true,
          ),
        ],
      ),
    ];

    expect(mappingRangeAt(models, 6), (start: 5, end: 8));
  });
}
