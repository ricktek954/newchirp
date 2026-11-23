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

The sidebar, the read and write confirmations and progress messages, the
read-only-driver notice, the incompatible-channel prompt, the channel apply
dialog (CSV/library import) and the radio settings write flow.

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
