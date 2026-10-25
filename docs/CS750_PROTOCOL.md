# Connect Systems CS750 experimental notes

These notes describe the interoperable facts used by the import-only
`newchirp_cs750.py` driver. The official CPS installer and extracted vendor
files remain outside this repository.

## Evidence

- CPS: CSI CPS R4.01.010 / host image S8.00.10
- Installer SHA-256:
  `e55ee07f245baf41e35b1a867e50b8c1c7e49f11938c4c08716aefa5ff8a2639`
- Main executable SHA-256:
  `72b1b767f1ab4b90dff1d4ecfe9975710269e5d992a738a9e25923fde1c8d023`
- Transport DLL SHA-256:
  `41bfcd749014ead133b396676ab39a4f292be2c592e635034280829183314758`
- Packet builder DLL SHA-256:
  `46df5405744b7fab1092f33be6c3e4bea01ef0cbac17fd38614242066838b4a7`

The analysis used REA with its supported Ghidra native-analysis line.

## Live transport

The CS750 programming interface is a USB mass-storage device, not a serial
port. The CPS identifies a removable drive whose SCSI vendor/product strings
are `STM     ` and `microSD Flash   `, opens the raw Windows drive, and sends
vendor SCSI passthrough commands.

The main read/write vendor command is SCSI operation code `0xFF`, with
subcommand `0x28` for read and `0x2A` for write. The command also contains the
ASCII marker `GP`.

NewChirp now has its own raw SCSI transport rather than using CHIRP's serial
bridge. The platform adapters are implemented in
`scripts/newchirp_mass_storage.py`. macOS uses the bundled IOKit helper in
`tools/newchirp_scsi_mac.c`; Windows uses `IOCTL_SCSI_PASS_THROUGH_DIRECT`;
Linux uses the generic `SG_IO` interface.

## RAP packet format

CPS command packets are:

```
A1 CMD_HI CMD_LO LEN_HI LEN_LO PAYLOAD SUM_HI SUM_LO A4
```

- `CMD` is a big-endian command identifier.
- `LEN` is the big-endian payload length.
- `SUM` is the big-endian 16-bit sum of the payload bytes.
- `A4` terminates the packet.

Response packets use the same framing. The read sequence implemented by
NewChirp is:

1. Send `0x0003` with no payload and read the 265-byte `0x8003` response.
2. Send `0x0015` with no payload and read the 10-byte `0x8015` response.
3. Require status payload byte 1 to be zero.
4. For each block, send `0x0010` with a 4-byte payload containing a big-endian
   block index followed by the page count `0x0008`, then read the 2063-byte
   `0x8010` response.
5. The first block reports the image size in 256-byte units at payload bytes
   3 through 6. Each response carries 2048 image bytes beginning at payload
   byte 7.

The CPS also contains `0x8017` responses on an authentication-dependent path.
NewChirp fails closed if that path is requested.

## Codeplug container

The supported 2,000-channel M100000 archive is 278,544 bytes (`0x44010`).

- `0x2000`: ASCII `CS750`
- `0x2010`: codeplug version, such as `D4.0.03`
- `0x2068`: model code `M100000`
- `0x21F60`: ordered channel count, little-endian `u16`
- `0x21F62`: ordered channel indices, little-endian `u16`
- `0xA000`: 16-byte alias table
- `0x12000`: 32-byte channel record table

Channel aliases use a 6-bit encoding. Three bytes encode four characters using
the alphabet `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .`.

The first 32-bit channel record fields are absolute RX and TX frequencies in
hertz. In the official sample, bit zero at record offset `0x08` distinguishes
the stock analog `ACH 1` channel from the stock digital `DCH 1` channel.

Other analog tone fields, DMR contact/talkgroup references, color codes, time
slots, scan lists, zones, and write checksums are not yet decoded.
