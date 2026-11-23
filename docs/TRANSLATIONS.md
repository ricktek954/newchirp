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

- Batch 1: the sidebar, the read and write confirmations and progress
  messages, the read-only-driver notice, the incompatible-channel prompt, the
  channel apply dialog (CSV/library import) and the radio settings write
  flow.
- Batch 2: channel table column titles and help, and the channel editor
  (field labels, tooltips, choice names, bulk-edit title and button).
- Batch 3: the radio connection page (steps, cable and model help, transfer
  buttons and image status), the radio model picker, the top bar (New, Open,
  Load module, Save, Print and Help menus) and the library toolbar (summary
  cards, search, add/duplicate, empty slots, filters, banks and zones,
  radio sections).
- Batch 4: the welcome screen, page headers, the About page and the radio
  settings page (status line, read/snapshot buttons, empty and error
  states). The GPL "WITHOUT ANY WARRANTY" sentence and the license page
  legalese stay in English as the authoritative license text.

Channel table column ids stay English (`_channelColumnTitle` translates at
display time), because saved column order, widths and filters key on them.
Choice values stay as stored; only their display names are translated. With
a radio connected, choices show the driver's own values (TSQL, +, -).

Not yet translated: channel validation messages (`RadioChannel.validate`),
the long "Channel editing" help text, row context menus, repeater search,
the frequency reference tables, and the bug-report dialog's labels (its
report body stays English). Setting names and values on the radio settings
page come from the CHIRP driver and stay English.

## Layout

Spanish and French labels run about a third longer than English. The top
bar and the library toolbar switch to their compact layouts at 1.4 times
the English widths for those languages. A widget test checks that Spanish
and French fit wherever English does in the test renderer; that renderer's
square glyphs are far wider than real fonts, so narrow windows (900-1100 px)
must be checked in the real app.

## What stays in English, on purpose

- Driver instructions, errors and setting names from CHIRP and the Python
  bridge, and the communication trace. These are what support reads.
- Bug-report contents and diagnostic logs.
- Model names, which follow the manufacturer's spelling.

## Adding a message

1. Add it to `app_en.arb`, with an `@key` block for any placeholders.
2. Add the Spanish and French text to the other two files. Leaving one out
   falls back to English and is listed in `build/l10n-untranslated.json`.
3. Keep radio terms consistent: es canal / zona / banco / repetidor,
   fr canal / zone / banque / relais. Use "la radio" in both.
4. Write and overwrite warnings must stay exact. If unsure of a translation,
   leave the English and flag it for review rather than guess.
