# TIDRADIO TD-H8 Fourth-Generation Serial Protocol

Last updated: 2026-11-08

## Artifact

- Official programmer: ODMaster Android `2.6.4` (`versionCode` 221)
- Package: `com.tid.walkie`
- Source: Google Play listing linked from
  `https://odmaster.tid-china.com/odmasterAppDownload`
- APK SHA-256:
  `52e6d0516f49de17f2869c800ef8fc84f41933b768e1205a0d7876705e2afdf5`
- Public protocol service:
  `https://odmaster.tid-china.com/protocol/readProtocol`
  and `https://odmaster.tid-china.com/protocol/wfDirect`
- The TD-H8 fourth-generation entries are named `TD-H8 4rd`,
  `TD-H8 4rd Ham`, and `TD-H8 4rd GMRS` by ODMaster.

The application uses Bluetooth LE through a programmer accessory. Its
application-level command encoding is the same binary clone protocol used by
pinned CHIRP for the TD-H8 family.

## Regional identities

| ODMaster profile | Identity returned after `02` | NewChirp class |
| --- | --- | --- |
| `TD-H8 4rd` | `54 44 48 38 34 47 45 4E` (`TDH84GEN`) | `TIDRadioTDH8FourthGen` |
| `TD-H8 4rd Ham` | `54 44 48 38 34 47 45 48` (`TDH84GEH`) | `TIDRadioTDH8FourthGenHAM` |
| `TD-H8 4rd GMRS` | `54 44 48 38 34 47 45 47` (`TDH84GEG`) | `TIDRadioTDH8FourthGenGMRS` |

ODMaster identifies the family with the TD-H3 magic
`50 56 4F 4A 48 5C 14` (`PVOJH\x5c\x14`). NewChirp detection continues to
use `PVOJH\x1c\x14` because that is the magic observed during successful G4
reads in NewChirp reports. Upload uses the ODMaster G4 magic.

## Read operation

ODMaster's G4 read template was compared for all three regional profiles. It
is identical apart from the regional identity above.

| Item | Recovered behavior |
| --- | --- |
| Entry magic | `50 56 4F 4A 48 5C 14` |
| Entry response | ACK `06` |
| Identity query | Host sends `02`; radio returns one of the eight-byte identities above |
| Clone ACK | Host sends `06`; radio returns `06` |
| Read request | `52 <address:u16be> <length:u8>` |
| Block size | `0x20` |
| Read response | `57 <address:u16be> <length:u8> <32-byte payload> <checksum>` |
| Read addresses | Sparse ODMaster map ending at `0x1F20` |
| End marker in template | `45` |

The current NewChirp read path intentionally retains its proven contiguous
read through the `0x1FEF` image boundary, which produced a complete
151-channel report.

## Write operation

`CommonWriteUtil.write()` provides the state machine:

1. Enable notifications, then send the entry magic.
2. On ACK `06`, send `02`.
3. On the identity response, send `06`.
4. On ACK `06`, send the first `W` page.
5. For every page ACK `06`, advance to the next page.
6. Stop immediately on any value other than ACK `06`.
7. ODMaster sends no final `E` command; closing the transport ends the
   programming session.

Each page is 37 bytes:

```text
57 <address:u16be> 20 <32-byte payload> <checksum>
```

The checksum is the unsigned sum of the 32 payload bytes modulo 256. The
header bytes are not included.

The same 170-page write set was generated for the Normal, Ham, and GMRS
profiles:

| Address interval | Page count | Purpose |
| --- | ---: | --- |
| `0x0000-0x1380` | 156 | Channel and channel-adjacent configuration memory |
| `0x1800-0x18E0` | 7 | General settings and startup data |
| `0x1900-0x1980` | 4 | Additional settings |
| `0x1C00-0x1C40` | 2 | VFO and operating state |
| `0x1F20-0x1F40` | 1 | Final exposed configuration page |

Pages outside those intervals are preserved. In particular, NewChirp does
not write the sparse read-only gaps, the unexposed tail through `0x1FEF`, or
any page based only on a third-generation layout assumption.

The generated ODMaster Ham write template contains 170 unique write frames
and hashes to
`aa1f896bafb7bc7f4536e6d992b333e17462800cf919bfd1f5326775c12436d0`.
The Normal and GMRS templates have the same address sequence and the same
checksum rule.

## Evidence and unresolved work

- E1: ODMaster 2.6.4 decompilation traced the UI route through
  `H8ReadUtil`, `CommonWriteUtil`, the public protocol service, page encoding,
  and ACK state machine.
- E2: Synthetic replay tests cover all three identities, the 170-page map,
  unchanged-byte reconstruction, incomplete images, model mismatch, and a
  bad page ACK.
- E4: A 2026-11-08 NewChirp 1.0.46 report completed a 151-channel physical
  read with `TDH84GEN`.
- E5: None yet. A controlled one-channel edit, upload, and read-back on a G4
  radio is still required before claiming hardware-validated writes.
- A physical OEM BLE/WebSerial capture would confirm whether ODMaster's
  apparent duplicate first-page send is a real wire event or an application
  callback artifact. NewChirp sends every official page once because duplicate
  writes provide no additional safety.
