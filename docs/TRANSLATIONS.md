# Interface translations

The desktop app supports English, Spanish (es) and French (fr). Status: beta,
started 2026-11-23. The Spanish and French text was drafted without a
native-speaker review; have a native speaker check it before calling either
language complete.

## How it works

- Messages live in `lib/l10n/app_en.arb` (template), `app_es.arb` and
  `app_fr.arb`. `flutter gen-l10n` (run automatically by `flutter run`,
  `flutter build` and `flutter test` because `pubspec.yaml` sets
  `generate: true`) writes `lib/l10n/app_localizations*.dart`.
- Use `context.l10n.<key>` (import `l10n/l10n.dart`).
- The app follows the computer's language. The sidebar's Language menu
  overrides it; the choice is saved in `language.json` next to the other
  preferences (`lib/services/app_language.dart`).
- macOS only reports languages listed in `CFBundleLocalizations`
  (`macos/Runner/Info.plist`). Add new languages there too.

## What is translated

Every screen and dialog of the desktop app (615 messages): sidebar,
welcome screen, radio connection, model picker, channel library and table,
channel editor, right-click menus, radio settings, frequency reference,
repeater search (RepeaterBook and myGMRS), banks/zones editor, marine
template, printing, updates, abbreviations glossary, About, and the bug
report dialog's labels.

`test/translations_test.dart` fails if Spanish or French is missing a
message or uses different placeholders from English.

Channel table column ids stay English (`_channelColumnTitle` translates at
display time), because saved column order, widths and filters key on them.
Choice values stay as stored; only their display names are translated. With
a radio connected, choices show the driver's own values (TSQL, +, -).

Most UI messages were moved by a script and have generated `ui…` keys; their
English text is unchanged.

## What stays in English, on purpose

- Driver instructions, errors and setting names from CHIRP and the Python
  bridge, and the communication trace. These are what support reads.
- Bug-report contents and diagnostic logs (the report summary, cable, radio
  and firmware fields and the "Reported error" body).
- Channel validation messages from `RadioChannel.validate` (model code with
  no UI context; tests depend on the wording) and exception messages the
  friendly-error code matches on.
- The GPL warranty sentence and license legalese (authoritative text).
- Radio model picker hints (top-level constant table), the radio prompt
  cue text matched against driver instructions, and data such as the default
  country and state.
- Model names, which follow the manufacturer's spelling.

## Adding a message

1. Add it to `app_en.arb`, with an `@key` block for any placeholders.
2. Add the Spanish and French text to the other two files. Leaving one out
   falls back to English and is listed in `build/l10n-untranslated.json`.
3. Keep radio terms consistent: es canal / zona / banco / repetidor,
   fr canal / zone / banque / relais. Use "la radio" in both.
4. Write and overwrite warnings must stay exact. If unsure of a translation,
   leave the English and flag it for review rather than guess.
