# module_sandbox

## Classs

- [ModuleSandbox](ModuleSandbox.md)
- [SandboxFiles](SandboxFiles.md)
- [SandboxLaunch](SandboxLaunch.md)

## Functions

- [_acceptedRoots](acceptedRoots.md)
- [_bubblewrapParents](bubblewrapParents.md)
- [_copyModule](copyModule.md) — Copies the user's module into the work folder as module.py / module.mod.
- [_ensureWork](ensureWork.md) — The private work folder (mode 700 = only this user), created on first use.
- [_findBubblewrap](findBubblewrap.md)
- [_isInside](isInside.md)
- [_pythonRoots](pythonRoots.md) — Folders the Python install lives in (sys.prefix and friends), resolved
- [_quote](quote.md)
- [_resolvePython](resolvePython.md) — Full path of the Python to run ("python3" is looked up with `which`).
- [_serialPort](serialPort.md) — The serial port to expose, or null if none; throws for unexpected names.
- [add](add.md) — Adds a folder (and its symlink target) once; ignores "" and "/".
- [addRoot](addRoot.md) — Allows executing/reading under [path] after checking it is a safe allow-root.
- [canLoadChirpModules](canLoadChirpModules.md) — True when this OS can sandbox a user-loaded CHIRP module at all.
- [currentSandboxPlatform](currentSandboxPlatform.md) — Which sandbox technology this OS uses (macOS Seatbelt, Linux bubblewrap, or none).
- [dispose](dispose.md) — Deletes the private work folder.
- [isSafeAllowRoot](isSafeAllowRoot.md) — A directory NewChirp may expose inside the sandbox.
- [isSafeSandboxPath](isSafeSandboxPath.md) — True for an absolute path that is safe to put in a sandbox profile: no quotes,
- [isSafeSerialPort](isSafeSerialPort.md) — True for a serial port name of the usual form (/dev/cu.* or /dev/tty.* on macOS,
- [linuxBubblewrapArguments](linuxBubblewrapArguments.md) — Linux bubblewrap (bwrap) arguments: an empty root with read-only system and
- [macosSeatbeltProfile](macosSeatbeltProfile.md) — macOS Seatbelt (sandbox-exec) profile. It starts from "allow default" ("deny
- [moduleSandboxBlocker](moduleSandboxBlocker.md) — Why a module can't be loaded right now, or null if it can. On Linux this
- [moduleSandboxEnvironment](moduleSandboxEnvironment.md) — Environment for the sandboxed helper: home and temp folders point at its
- [ModuleSandboxException](ModuleSandboxException.md)
- [moduleSandboxRefusal](moduleSandboxRefusal.md) — A message when this operating system cannot sandbox a module at all.
- [mount](mount.md) — Bind-mounts [source] at the same path ([mode] = --bind or --ro-bind),
- [prepare](prepare.md) — Prepares a sandboxed launch: private work folder, copies of the module and
- [replaceModuleArgument](replaceModuleArgument.md) — Copy of the helper's arguments with the --module path replaced by [modulePath].
- [requireFile](requireFile.md) — Throws unless [path] is a safe file path to expose.
- [requireRoot](requireRoot.md) — Throws unless [path] is an acceptable folder to expose.
- [sandboxFilesIn](sandboxFilesIn.md) — The image, channels, settings and port files named in the helper's arguments.
- [toString](toString.md)
