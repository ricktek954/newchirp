"""Read-only support for the Radtel RT-860.

The RT-860 uses the same iRadio/Iradio-family serial transport and
memory layout as the Radtel RT-880G.  The sparse read plan below was
recovered from the official RT-860 CPS V1.06 and intentionally mirrors
the OEM application instead of downloading unused address ranges.
"""

import logging
import time

from chirp import chirp_common, directory, errors, memmap
from chirp.drivers.radtel_rt880g import RT880G
from chirp.drivers.radtel_rt880g import RT880GBank
from chirp.drivers.radtel_rt880g import RT880GBankModel
from chirp.drivers.radtel_rt880g import _read_block


LOG = logging.getLogger(__name__)

IMAGE_SIZE = 0xD5000
BLOCK_SIZE = 0x400

# (logical offset, first physical page, page count)
READ_REGIONS = (
    (0x00000, 0x008, 4),    # settings
    (0x02000, 0x010, 48),   # 1024 channels
    (0x1A000, 0x070, 128),  # 256 zones
    (0xD4000, 0x358, 4),    # 128 broadcast memories
)
READ_PAGE_COUNT = sum(count for _offset, _page, count in READ_REGIONS)

ENTER_MAGIC = b"4R\x05\x10\x9b"
EXIT_MAGIC = b"4R\x05\xee\x79"

POWER_LEVELS = [
    chirp_common.PowerLevel("Low"),
    chirp_common.PowerLevel("High"),
    # The CPS only defines Low (0) and High (1). Keep a third alias for
    # compatibility with the inherited RT-880G decoder's legacy value 2.
    chirp_common.PowerLevel("High"),
]


def _decode_text(raw):
    raw = raw.split(b"\x00", 1)[0]
    while raw.endswith((b"\xff", b" ")):
        raw = raw[:-1]
    return raw.decode("gb18030", errors="replace")


class RT860Bank(RT880GBank):
    def get_name(self):
        offset = 0x1A000 + self.index * 512 + 4
        return _decode_text(self._model._radio._mmap.get(offset, 16))

    def set_name(self, name):
        offset = 0x1A000 + self.index * 512 + 4
        encoded = str(name).encode("gb18030", errors="replace")[:16]
        self._model._radio._mmap.set(offset, encoded.ljust(16, b"\xff"))


class RT860BankModel(RT880GBankModel):
    def get_mappings(self):
        banks = []
        for index in range(256):
            bank = RT860Bank(self, "%i" % index, "b%i" % (index + 1))
            bank.index = index
            banks.append(bank)
        return banks


@directory.register
class RT860Radio(RT880G, chirp_common.ExperimentalRadio):
    """Radtel RT-860 experimental read-only driver."""

    VENDOR = "Radtel"
    MODEL = "RT-860"
    BAUD_RATE = 115200
    WANTS_DTR = True
    WANTS_RTS = False
    HARDWARE_FLOW = False
    XON_XOFF = False
    POWER_LEVELS = POWER_LEVELS

    SPECIALS = {}

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.experimental = (
            "The Radtel RT-860 driver is experimental and read-only. It "
            "downloads the channel and zone blocks used by the official "
            "CPS, but uploads are disabled until the CPS write sequence is "
            "verified on physical hardware."
        )
        prompts.info = (
            "Connect the radio's USB programming cable, turn the radio on, "
            "and start the download. The CPS uses 115200 baud, 8 data bits, "
            "no parity, one stop bit, and DTR asserted."
        )
        prompts.pre_download = (
            "1. Turn the radio on and connect its USB programming cable.\n"
            "2. Close the Radtel RT-860 CPS so it does not hold the serial "
            "port.\n"
            "3. Start the download and leave the radio powered on.\n\n"
            "This driver is read-only. Do not attempt an upload."
        )
        return prompts

    def get_features(self):
        features = super().get_features()
        features.has_settings = False
        features.valid_special_chans = []
        features.valid_power_levels = POWER_LEVELS[:2]
        return features

    def _reset_serial_buffers(self):
        for name in ("reset_input_buffer", "reset_output_buffer"):
            reset = getattr(self.pipe, name, None)
            if reset is not None:
                reset()

    def _enter_programming_mode(self):
        previous_timeout = getattr(self.pipe, "timeout", None)
        self._reset_serial_buffers()
        self.pipe.timeout = 0.25
        try:
            for attempt in range(3):
                self.pipe.write(ENTER_MAGIC)
                if self.pipe.read(1) == b"\x06":
                    return
                if attempt < 2:
                    time.sleep(0.2)
                    self._reset_serial_buffers()
        finally:
            if previous_timeout is not None:
                self.pipe.timeout = previous_timeout
        raise errors.RadioNoResponse(
            "The RT-860 did not acknowledge programming mode"
        )

    def set_memory(self, memory):
        name = memory.name
        # CHIRP's inherited RT-880G encoder treats characters as bytes. Encode
        # the GBK name separately after the shared fixed-width fields are
        # written, while giving the base writer an ASCII placeholder.
        memory.name = ""
        try:
            super().set_memory(memory)
        finally:
            memory.name = name
        if not memory.empty:
            raw = self._get_memobjs(memory.number)
            if int(raw.power):
                raw.power = 1
            offset = 0x2000 + (memory.number - 1) * 48 + 32
            encoded = name.encode("gb18030", errors="replace")[:16]
            self._mmap.set(offset, encoded.ljust(16, b"\xff"))

    def get_memory(self, number):
        memory = super().get_memory(number)
        if not memory.empty:
            if int(self._get_memobjs(number).enabled) != 1:
                memory = chirp_common.Memory()
                memory.number = number
                memory.empty = True
                return memory
            offset = 0x2000 + (number - 1) * 48 + 32
            memory.name = _decode_text(self._mmap.get(offset, 16))
        return memory

    def get_bank_model(self):
        return RT860BankModel(self)

    def sync_in(self):
        memory = memmap.MemoryMapBytes(b"\xff" * IMAGE_SIZE)
        session_started = False
        old_timeout = getattr(self.pipe, "timeout", None)

        try:
            self._enter_programming_mode()
            session_started = True
            self.pipe.timeout = 1.0

            page_number = 0
            for logical_offset, first_page, count in READ_REGIONS:
                for page in range(first_page, first_page + count):
                    page_number += 1
                    status = chirp_common.Status()
                    status.cur = page_number
                    status.max = READ_PAGE_COUNT
                    status.msg = "Reading RT-860 memory"
                    self.status_fn(status)

                    block = _read_block(self, page, BLOCK_SIZE)
                    offset = logical_offset + (
                        page - first_page
                    ) * BLOCK_SIZE
                    memory.set(offset, block)
        except errors.RadioError:
            raise
        except Exception as exc:
            raise errors.RadioError(
                "Failed to communicate with the RT-860: %s" % exc
            ) from exc
        finally:
            if old_timeout is not None:
                self.pipe.timeout = old_timeout
            if session_started:
                try:
                    self.pipe.write(EXIT_MAGIC)
                    time.sleep(0.01)
                except Exception:
                    pass

        self._mmap = memory
        self.process_mmap()

    def sync_out(self):
        raise errors.RadioError(
            "The Radtel RT-860 driver is read-only until the official CPS "
            "write sequence has been verified on physical hardware."
        )
