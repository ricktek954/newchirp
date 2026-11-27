# app_language

## Functions

- [_defaultPath](defaultPath.md)
- [AppLanguageStore](AppLanguageStore.md)
- [load](load.md) — Reads the saved choice; returns "system" when nothing is saved or the file is unreadable.
- [localeForLanguageCode](localeForLanguageCode.md) — The [Locale] for a supported language code, or null for "system" or an unknown code.
- [save](save.md) — Saves the choice. Failures are ignored: the language just won't be remembered.
