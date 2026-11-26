# Reverse-engineering tools

Tools for recovering a radio protocol from its OEM programming software
(CPS). Read `docs/REA_PLAYBOOK.md` first: it defines the evidence classes
(static, replay, OEM capture, physical radio) and what each can prove.
Never run an OEM installer or CPS on the host; DOS programs run in the
FreeDOS VM below, and Windows installers are only unpacked.

Downloaded CPS files are untrusted: keep each in its own empty directory
and run Python on them with `-I`.

## Unpacking Windows installers (`installers/`)

Inno Setup 6.3+ installers defeat innoextract 1.9.

1. `inno_carve.py SETUP.exe OUTDIR` finds `zlb\x1a` chunks and decodes
   them with Python's own raw LZMA1 decoder.
2. `pe_split.py OUTDIR/chunk_*.bin PEDIR` cuts the chunk into the PE files
   it contains, using each PE's section table for its length.
3. `inno_uncall.py PEDIR/pe_X.bin FIXED.exe` reverses Inno's
   `TransformCallInstructions` (E8/E9 relative addresses, 64 KB buffers).
   Without it, .NET decompilation shows "Invalid field token" and broken
   method bodies.

Then decompile .NET assemblies with `ilspycmd -p -o SRC FIXED.exe`.
Example: UV-5RM Pro seller CPS "5RH Pro v1.12" -> CPS.exe 1.0.1.2,
SHA-256 `3e8f7c42...` (docs/BAOFENG_5RH_PRO_PROTOCOL.md).

## DOS programs in QEMU (`qemu_dos/`)

`run_cps.sh BOOT.img CPSDIR trace.log` boots FreeDOS 1.4 (floppy edition)
with the CPS folder as C: and COM1 on 127.0.0.1:47350, tracing UART
register writes and reads (baud, framing, every byte). `keys.py` types
keystrokes and takes screenshots through the monitor socket.

Tips learned the hard way:

- macOS limits socket paths to 104 bytes: run from the working directory
  and use the relative `mon.sock`.
- DOS menus drop keys sent right after opening them: send `@alt-f` and the
  arrow keys in separate `keys.py` calls, and screenshot before acting.
- Text fields overtype: clear old text with `@delete`s.
- After restarting a simulator the CPS's first command can be lost; choose
  Retry once.
- INT 14h: a real BIOS raises DTR+RTS while sending and DTR while
  receiving; SeaBIOS does not touch MCR, so "no MCR writes" in the trace
  does not mean the lines are off.
- To find a data layout, type known values into the CPS, save the file,
  and diff it. Built-in "test frequency" tables give free ground truth.

## Radio simulators (`simulators/`)

`kpg23d_radio.py` (TK-250/TK-350) and `kpg32d_radio.py` (TK-259/TK-359)
answer reads and writes as the traced radios do and log every byte, with
options for failure cases (wrong identity, NAK, fill replies). Use them as
templates: start by logging everything and answering nothing, then add
replies until the CPS reports success, and confirm the result with a
byte-for-byte comparison against the file the CPS sent.

## Binary analysis (`dos/`, `capture/`)

- `dos/xrefs.py` finds strings, data references, near calls and INT 14h
  sites in a DOS MZ executable; `dos/dis16.py` disassembles a range
  (capstone in a venv).
- `capture/usbpcap_serial.py` prints the serial bytes in a USBPcap
  capture, with `--ftdi` to strip FTDI status bytes.

Evidence from the KPG-23D/KPG-32D work is in `docs/evidence/kpg/`.
