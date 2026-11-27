# radio_model_picker

## Classs

- [_ModelChoice](ModelChoice.md)
- [_ModelEntry](ModelEntry.md)
- [_ModelResultsList](ModelResultsList.md)
- [_ModelResultsListState](ModelResultsListState.md)
- [_RadioModelDialog](RadioModelDialog.md)
- [_RadioModelDialogState](RadioModelDialogState.md)
- [_RadioModelPickerState](RadioModelPickerState.md)
- [_SectionHeader](SectionHeader.md)
- [_VendorChoice](VendorChoice.md)
- [_VendorHeading](VendorHeading.md)
- [_VendorModels](VendorModels.md)
- [RadioModelPicker](RadioModelPicker.md)

## Functions

- [_cacheGroups](cacheGroups.md) — Stores [groups] as the cached result for [query] and the current vendor.
- [_groupModels](groupModels.md) — Groups models by vendor (from CHIRP's vendor list when available), sorted.
- [_matchingGroups](matchingGroups.md) — Groups to show for the current search text and vendor filter (cached while
- [_modelNameWithinVendor](modelNameWithinVendor.md) — Model name without the vendor prefix, for rows listed under that vendor.
- [_modelSearchText](modelSearchText.md) — Everything the picker search matches against: official name, CHIRP spelling,
- [_openPicker](openPicker.md) — Opens the full model catalog dialog and reports the choice.
- [_remember](remember.md) — Moves [model] to the front of the recent list, keeping at most [_maxRecentModels].
- [_selectVendor](selectVendor.md) — Filters the catalog to one vendor (null = all) and clears the search.
- [_submitSearch](submitSearch.md) — Enter in the search box picks the first matching model.
- [_vendorSlug](vendorSlug.md)
- [build](build.md)
- [createState](createState.md)
- [didUpdateWidget](didUpdateWidget.md)
- [displayRadioModelName](displayRadioModelName.md) — Name shown to people: the manufacturer's official spelling (e.g. "DR-735T")
- [dispose](dispose.md)
- [initState](initState.md)
