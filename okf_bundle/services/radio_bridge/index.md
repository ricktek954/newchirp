# radio_bridge

## Classs

- [RadioCapabilities](RadioCapabilities.md)
- [RadioInstructions](RadioInstructions.md)
- [RadioModelCatalog](RadioModelCatalog.md)
- [RadioModelGroup](RadioModelGroup.md)
- [RadioProgress](RadioProgress.md)
- [RadioSettings](RadioSettings.md)
- [RadioZone](RadioZone.md)
- [SerialPortInfo](SerialPortInfo.md)
- [UndecodedChannel](UndecodedChannel.md) — A channel slot the driver could not decode. The bridge leaves it out of

## Functions

- [_bundledAssetCandidates](bundledAssetCandidates.md) — Places an asset file may be on disk: the working folder, then this platform's
- [_bundledResourcesDirectory](bundledResourcesDirectory.md) — The app bundle's resources folder (macOS Contents/Resources), or null elsewhere.
- [_deduplicatePorts](deduplicatePorts.md) — Drops repeated port names, keeping the first.
- [_findChirpSource](findChirpSource.md) — CHIRP source folder: the configured path or CHIRP_SOURCE, else the copy
- [_findLibusbRuntime](findLibusbRuntime.md) — The bundled libusb library (for USB radios), if found.
- [_findNewChirpDrivers](findNewChirpDrivers.md) — NewChirp's own drivers folder: the settings or NEWCHIRP_DRIVERS, else
- [_findScsiHelper](findScsiHelper.md) — The SCSI helper used for USB mass-storage radios on macOS, if found.
- [_firmwareFromPayload](firmwareFromPayload.md) — Firmware version reported by the bridge, or null when it sent none.
- [_loadAssetBytes](loadAssetBytes.md) — Asset bytes, cached; falls back to reading the file from known install locations.
- [_loadRootBundleAsset](loadRootBundleAsset.md) — The bundled libusb library (for USB radios), if found.
- [_massStoragePortDetails](massStoragePortDetails.md) — Radios that appear as USB mass-storage devices, as reported by the bridge;
- [_materializeBridge](materializeBridge.md) — Writes chirp_bridge.py and its helper scripts from the app's assets into [runtime].
- [_materializePythonDependencies](materializePythonDependencies.md) — Writes the bundled pyserial wheel into [runtime] (Python imports it from there).
- [_parseComPorts](parseComPorts.md) — COM port names (COM1, COM12...) found at the end of each output line.
- [_resolvePython](resolvePython.md) — The bundled CHIRP tree uses Python 3.10+ syntax, so prefer an interpreter
- [_run](run.md) — Runs one bridge command in a fresh temp folder that is deleted afterwards.
- [_runWithRuntime](runWithRuntime.md) — Starts the Python bridge with CHIRP and NewChirp's drivers, streams progress
- [_windowsSerialPortDetails](windowsSerialPortDetails.md) — Windows COM ports with their device names (looked up with PowerShell).
- [_windowsSerialPortNames](windowsSerialPortNames.md) — Windows: read the live COM ports from the SERIALCOMM registry key, then
- [cancelActive](cancelActive.md) — Asks the running bridge process to stop (SIGTERM). True when nothing is running
- [download](download.md) — Reads the radio on [port] and saves its image; returns the channels and the
- [imageCapabilities](imageCapabilities.md) — Just the capabilities of an image.
- [imageInfo](imageInfo.md) — Capabilities, model and zone list of an image without decoding its channels.
- [instructions](instructions.md) — Driver instructions for [model] (info, experimental warning, steps before
- [isBenignBridgeStderrLine](isBenignBridgeStderrLine.md) — True for harmless stderr lines (CHIRP's "Replacing existing driver id" notice
- [loadBundledAsset](loadBundledAsset.md) — The bundled libusb library (for USB radios), if found.
- [loadModule](loadModule.md) — Loads a user-supplied CHIRP driver (.py or .mod); it then runs in the module
- [modelCatalog](modelCatalog.md) — Model ids plus vendor groups, from the bridge's list-models command.
- [models](models.md) — CHIRP model ids the bridge can program.
- [parseWindowsSerialPortDetails](parseWindowsSerialPortDetails.md) — The bundled libusb library (for USB radios), if found.
- [RadioBridge](RadioBridge.md)
- [RadioBridgeException](RadioBridgeException.md)
- [radioBridgeFailureMessage](radioBridgeFailureMessage.md) — User-facing message for a bridge process that exited with [exitCode];
- [RadioSettingNode](RadioSettingNode.md)
- [readImage](readImage.md) — Channels, capabilities and zones/banks from a saved radio image (optionally
- [readSettings](readSettings.md) — Reads the radio's settings from an image or a port (exactly one of the two).
- [resolvePythonExecutable](resolvePythonExecutable.md)
- [searchRepeaters](searchRepeaters.md) — RepeaterBook search through the bridge.
- [serialPortDetails](serialPortDetails.md) — Serial ports (with device names where the OS gives them) plus USB mass-storage
- [serialPorts](serialPorts.md) — Just the port names from [serialPortDetails].
- [strings](strings.md) — The JSON list [key] as strings (empty when missing).
- [toChangeJson](toChangeJson.md) — The bundled libusb library (for USB radios), if found.
- [toString](toString.md) — The bundled libusb library (for USB radios), if found.
- [undecodedChannelsFromJson](undecodedChannelsFromJson.md) — Parses the bridge's list of channel slots it could not decode.
- [unloadModule](unloadModule.md) — Stops using the loaded module and deletes its sandbox work folder.
- [upload](upload.md) — Writes [channels] (and cleared slots and zone changes) into the image and
- [writeSettings](writeSettings.md) — Applies setting [changes] to the image and writes it to the radio.
