# TIDRADIO TD-H8 CPS Analysis

Last updated: 2026-11-14

## Official artifacts

TIDRADIO's portal still serves the TD-H8 HAM, GMRS, and Unlock packages from
its hidden download route at
`https://www.walkietalkiesoftware.com/portal/index/download/id/89.html`:

- `https://tidodmaster.oss-us-west-1.aliyuncs.com/H8/H8%20ham.zip`
- `https://tidodmaster.oss-us-west-1.aliyuncs.com/H8/H8%20gmrs.zip`
- `https://tidodmaster.oss-us-west-1.aliyuncs.com/H8/TD-H8%20Unlock.zip`

| Package | SHA-256 |
| --- | --- |
| `H8 ham.zip` | `449fe6fcfa21ca5511c6095e2e3f27e24477b6b15a90ddf658bb4f7f3383423c` |
| `H8 gmrs.zip` | `ec418755a7107a392d701b090e13b354307280291fc0a58c8cfb3e65a0e8f16c` |
| `TD-H8 Unlock.zip` | `4dd0c5518dc81474c4e0a807d1e5f2e54bf07cb3a07771e46c5a8933ee6932b0` |

The HAM programmer is
`TIDRADIO_H8(HAM)_setup230329.exe`, SHA-256
`c58e7829da8748e979a8aaa88a56513e4592c95154ad12f65255b60a90cd785c`.
It is a Setup Factory 8 package. Its embedded programmer was extracted
statically without executing the installer. The extracted
`TIDRADIO_H8(HAM).exe` SHA-256 is
`490d86c8feece949b20db20d8200c502f3681ca7cb2f9fd09240d161880d2b22`
when the installer is extracted with the reviewed
`CybercentreCanada/sfextract` parser at commit
`21f5c5595a70e9284fff83476c0e307d5b92f573`, plus an output-directory
containment guard.

TIDRADIO's current 2026 multi-model CPS archive is
`TIDRadioCPS__20260123.zip`, SHA-256
`7fc35af45009ec455b6aabf638d3ea030a6044b24b5712dce11e2b65032e6a03`.
That package contains profiles only for H3 Plus and H9; it does not contain a
newer TD-H8 profile. It is published from
`https://cdn.shopify.com/s/files/1/0096/6479/0607/files/TIDRadioCPS__20260123.zip`.

## Recovered evidence

- The official HAM CPS contains the unqualified TD-H8 entry magic
  `50 56 4F 4A 48 1C 14` (`PVOJH\x1c\x14`) at file offset `0x63F20`.
- Its serial state machine copies that seven-byte value into its transmit
  buffer and retries the programming entry up to five times.
- The same table contains the TD-H8 band limits: 136-174 MHz and 400-480 MHz.
- The byte following the magic begins a local band descriptor used by the
  CPS's frequency editor. The CPS also contains the same three power-level
  names and channel-field terminology exposed by CHIRP.
- The official HAM package does not contain the Gen 3 variant magic
  `PVOJH\x3c\x14` used by CHIRP's `TD-H8-HAM_G3` entry.
- The pinned CHIRP `tdh8.py` is byte-identical to current upstream at SHA-256
  `6cc013c387f4728df4db826cd758fad805fd855e43bc44e70e2004aac845cc6c`.

This proves the official CPS entry identity and band values. It does not by
itself prove a complete NewChirp Gen 3 write transport, and no physical
write/read-back has been performed. Do not infer hardware validation from the
static extraction.

## Reported 542-channel write failure

The 2026-11-14 report used `TIDRADIO_TD-H8` after `TD-H8-HAM_G3` received no
entry response. The unqualified driver read 55 channels successfully. The
later upload contained 542 imported channels, while this driver exposes memory
locations 1 through 199.

NewChirp now:

- removes incompatible channels when the user chooses
  `Skip and write remaining`;
- validates locations against `memory_bounds` before calling a driver's
  `get_memory()` or `set_memory()`;
- reports out-of-range channels as skipped instead of retrying unsafe writes;
- adds channel and field context to unexpected driver preparation failures;
- caps the post-write findings dialog so hundreds of skipped channels do not
  create an unbounded UI.

The regression test loads the upstream TD-H8 image, prepares 542 synthetic
channels, writes locations 1-199, and verifies that locations 200-542 are
skipped without touching the driver.
