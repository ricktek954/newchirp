# nicFW950 memory programming

The experimental `drivers/newchirp_nicfw950.py` driver programs memory on
RT-950 Pro / BJ-9000 radios already running nicsure nicFW950 with the
supplied 999-channel flash layout. It does not install firmware.
The stock RT-950 driver remains a
separate, read-only driver with a different protocol and image format.

Catalog entries:

- `Radtel_RT-950_Pro_nicFW950`
- `Bajeton_BJ-9000_nicFW950`

The protocol/layout reference is the user-provided `nicfw_950_v4.py` with
SHA-256 `bb20f6252dba38bfa604f2ba0c0e465f0d98c67b73d1cfdc5071576dfdcc1f45`.
The standalone reference was not executed. The NewChirp port was validated
on one user-provided unit with **nicFW950 6.00.16c** on 2026-10-31.
Other firmware versions and individual aliases still need validation.

The standard RT-950 (non-Pro) is excluded. Nicsure's
[release hub](https://www.patreon.com/nicsure/posts/central-hub-150725357)
lists the RT-950 Pro. His
[Pro backup/restore firmware post](https://www.patreon.com/nicsure/posts/radtel-rt-950-160721095)
also explicitly leaves compatibility of that tool with non-Pro hardware
unknown. Neither the supplied CHIRP reference nor the physical test provides
evidence for a separate non-Pro nicFW950 catalog entry.

## Serial protocol

All addresses and integers below are little endian. Serial is 8N1, without
hardware or software flow control.

| Operation | Request | Response |
| --- | --- | --- |
| Negotiate baud | `AA 70 <u32 460800> 55` at 38400 baud | `AA 70`, then a second `AA 70` at 460800 baud |
| Read 128 bytes | `AA 30 <u32 address> 55` | `AA 30 <u32 address> <128 bytes> <checksum>` |
| Stage 128 bytes | `AA 40 <u32 address> <128 bytes> <checksum> 55` | `AA 40` |
| Commit flash | `AA 48 55` | `AA 48`, with a 15-second timeout |
| Reboot without saving RAM settings | `AA 50` (exactly two bytes) | No ACK expected |

The checksum is the sum of the four address bytes and 128 data bytes, modulo
256. Read replies must have the expected header, echoed address and checksum.
Fragmented replies are accumulated; an empty serial read is a timeout.
Restore the host baud rate to 38400 after success or failure. The reference
states the radio returns to 38400 after its idle timeout.
An immediate new operation can precede that reset. If the initial baud ACK
times out, wait three quiet seconds and retry once at 38400. Bad ACKs,
high-speed ACK failures, flash writes and flash commits are not retried.

## Image and editable fields

The raw image covers `0x50200..0x5FCFF` inclusive: `0xFB00` (64,256) bytes,
or 502 blocks. Saved `.img` files also carry CHIRP model metadata.

| Region | Address / layout | Policy |
| --- | --- | --- |
| Reserved/VFO records | First four 62-byte records at `0x50200` | Preserve |
| Channels 1–999 | 62-byte records starting at image offset 248 | Editable |
| Channel padding | End of channel records to `0x5F5FF` | Preserve |
| Global settings | `0x5F600`, 1024 bytes | Only edited exposed settings |
| Calibration / power-band region | `0x5FA00..0x5FAFF` | Preserve |
| Group names | `0x5FB00`, 512 bytes | Slots 1–26 only |

Channel record fields are RX/TX frequency (u32, 10 Hz units), four group
bytes, RX/TX subtone (u16), signed clarifier, modulation, bandwidth, busy lock,
power, reverse, PTT-ID, magic `0xC950`, scrambler, scan-persist override,
scan-monitor override, permanent flag, two reserved bytes and a 30-byte name.
Invalidating a channel changes only its magic field.

DCS uses `0x8000` plus the binary value of the octal designation; `0x4000`
selects reversed polarity. For example D114 is `0x804C`, or `0xC04C` reversed.
CTCSS is stored in tenths of Hz; zero means no tone.

The Comment column contains up to four A-Z group letters, one per stored byte
(1–26). Each group-name slot is 13 bytes: marker `0xAA` and twelve
space-padded ASCII characters. Slot zero, unnamed slots and unused bytes are
preserved unless an exposed name is explicitly edited.

The shared Mode field exposes FM, NFM and AM. Native DSB and Automatic
modulation/bandwidth are available in channel extras and survive unrelated
edits. The seven power labels come from the reference and are not wattage
measurements. Scan-skip is not supported by this layout.

The global settings table follows the supplied reference, covering squelch,
scanning, VFO, display, DTMF/MDC1200, time, GPS, advanced and APRS settings.
Unknown/out-of-range values display defaults but are not rewritten by an
unrelated settings edit.

## Upload policy

Every loaded image establishes a baseline before edits, including when the
bridge starts a fresh process for an upload. Re-parsing settings does not
reset that baseline. No changed blocks means no serial transaction.

Before any write, reject modified protected regions and read all affected
blocks from the radio. If any differs from its baseline (including adjacent
bytes), stop and request a fresh download. This prevents stale block writes;
it is not a unique radio identity check. The supplied protocol has no
firmware-version or hardware-identity query.

Stage only changed 128-byte blocks, require the flash-commit ACK, then issue
the two-byte reboot. Failed transfers do not advance the image baseline or
report success. The commit ACK is protocol confirmation; an independent
post-reboot download is still required for physical validation. The driver
does not call wxPython or create modal dialogs in the headless bridge.

## Verification

With the pinned CHIRP source downloaded by `scripts/update_chirp.sh`, run:

```sh
python -m unittest test.nicfw950_driver_test -v
```

The synthetic serial peer checks framing, checksums, fragmented reads,
baud negotiation, all 502 read addresses, changed-block upload, stale-block
rejection, protected bytes, failed ACKs, commit/reboot ordering and no-op
uploads. Tests also exercise CHIRP image save/reload and the actual NewChirp
bridge JSON channel/settings upload paths. Synthetic tests cannot establish
that a particular firmware version or physical radio is compatible.

For further hardware validation, perform and record this sequence:

1. Record the radio model and exact nicFW950 version. Close CHIRP/RMS and
   other serial programs. Use the USB programming cable and normal power-on.
2. Choose the **nicFW950** model variant, select the cable's COM port, read
   the radio and keep an untouched original `.img` backup.
3. Compare channel count, names, frequencies, tones, groups and selected
   settings with the radio. Record the original raw-image SHA-256.
4. Change one existing channel name, upload, wait for completion/reboot,
   then read the radio again. Compare the entire raw image with the expected
   edited image and verify calibration/power-band/reserved bytes are unchanged.
5. Test one settings edit and one group-name edit separately, re-reading
   after each. Record any radio-managed differences instead of silently
   accepting them. Restore the edited fields and verify again.
6. Add the evidence and firmware coverage to `docs/DRIVER_STATUS.md`.

## Recorded hardware validation: 6.00.16c

One user-provided unit already running nicFW950 was tested with the NewChirp
1.0.30 Windows runtime and this maintained driver on 2026-10-31:

- Complete download: 502 checked blocks, 64,256 raw bytes, 209 occupied channels.
- No-op decode/re-encode of all occupied channels and global settings:
  zero changed bytes.
- Channel 1 name changed and independently read after reboot: full image
  matched the expected image. The original 30-byte name, including padding,
  was restored.
- Squelch changed from 5 to 6 and group A renamed separately: each full
  post-reboot image matched its expected image. Both original values were
  restored and re-read.
- The user selected slot B, channel mode and channel 1 during the test.
  Three operating-state bytes changed outside the name write and were
  retained. Final image equaled the subsequent stable baseline byte-for-byte;
  all channels, reserved/VFO records, calibration and power-band data matched
  the original download.
- Immediate renegotiation after a download exercised the recovery path:
  two baud requests, one three-second quiet interval, 4.783 seconds total.
- The firmware left FM Receive Method unset (`0xFFFF`); default display did
  not rewrite it during unrelated settings edits.

Raw-image SHA-256 evidence (images remain private, outside the repository):

| Image | SHA-256 |
| --- | --- |
| Original download | `a928d10955de1096f5d99f2cfc07687695c0a2a23adb5f16b6a570003fb02ee6` |
| Channel-name readback | `609abc2b656aa1575c82cb84f7e1b90a4178f21f6efa26d8e4cc5f0edc574d83` |
| Squelch readback | `073386da54a810fbf7d7b13bb6a66c1256982f91796e962ab691c4ddb49d4464` |
| Group-name readback | `2107d65cbafa96b7bdb97bc2692d6ac586f0425fd360518b1c7607d7483d6e55` |
| Final restored image, with user's operating-state changes | `7514da597c1793c18731cbb3d4fc5958883c1ff3b508864c55b6841e82425339` |
