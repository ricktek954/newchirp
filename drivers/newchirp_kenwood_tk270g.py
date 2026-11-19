# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""NewChirp-maintained Kenwood TK-270G driver.

The Series 60G wire protocol and memory layout are based on the pinned CHIRP
implementation. This driver owns the channel read/write path so bank metadata
cannot be converted into inverted booleans.
"""

from chirp import chirp_common, directory, errors
from chirp.drivers import tk760g
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueBoolean,
    RadioSettingValueInteger,
)


_BANK_SETTINGS = {"bank", "bnumb"}
WRITE_ACK_RETRIES = 3


def _extra_integer(memory, name):
    for setting in memory.extra:
        if setting.get_name() == name:
            return int(setting.value)
    return None


def _normalized_bank_metadata(channel, number):
    bank = int(channel.bank)
    bank_index = int(channel.bnumb)
    if not 1 <= bank <= 128:
        bank = 1
    if not 0 <= bank_index <= 127:
        bank_index = number - 1
    return bank, bank_index


@directory.register
class NewChirpTK270G(tk760g.TK270G_Radios):
    """Kenwood TK-270G with safe NewChirp bank handling."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "This is NewChirp's experimental TK-270G driver. Before writing, "
            "save a complete KPG-56D backup and keep a second copy. After "
            "writing, power-cycle the radio and read it back before relying "
            "on it."
        )
        return prompts

    def get_memory(self, number):
        _mem = self._memobj.memory[number - 1]
        raw = _mem.get_raw(asbytes=True)
        try:
            mem = chirp_common.Memory()
            mem.number = number

            if _mem.rxfreq[0].get_raw(asbytes=True) == b"\xFF":
                mem.empty = True
                return mem

            bank, bank_index = _normalized_bank_metadata(_mem, number)
            mem.freq = int(_mem.rxfreq) * 10
            if _mem.get_raw(asbytes=True)[16] == 0xFF:
                mem.offset = 0
                mem.duplex = "off"
            else:
                offset = (int(_mem.txfreq) * 10) - mem.freq
                if offset < 0:
                    mem.offset = abs(offset)
                    mem.duplex = "-"
                elif offset > 0:
                    mem.offset = offset
                    mem.duplex = "+"
                else:
                    mem.offset = 0

            mem.name = str(_mem.name).rstrip(" \xff")
            mem.power = tk760g.POWER_LEVELS[_mem.power]
            mem.mode = tk760g.MODES[_mem.wide]
            mem.skip = self._get_scan(number - 1)

            txtone = self._decode_tone(_mem.tx_tone)
            rxtone = self._decode_tone(_mem.rx_tone)
            chirp_common.split_tone_decode(mem, txtone, rxtone)

            mem.extra = RadioSettingGroup("extra", "Extra")
            mem.extra.append(
                RadioSetting(
                    "bank",
                    "Bank",
                    RadioSettingValueInteger(1, 128, bank),
                )
            )

            mem.extra.append(
                RadioSetting(
                    "bnumb",
                    "Bank index",
                    RadioSettingValueInteger(0, 127, bank_index),
                )
            )
            mem.extra.append(
                RadioSetting(
                    "beat_shift",
                    "Beat shift",
                    RadioSettingValueBoolean(not bool(_mem.beat_shift)),
                )
            )
            mem.extra.append(
                RadioSetting(
                    "compander",
                    "Compander",
                    RadioSettingValueBoolean(not bool(_mem.compander)),
                )
            )
            mem.extra.append(
                RadioSetting(
                    "busy_lock",
                    "Busy Channel lock",
                    RadioSettingValueBoolean(not bool(_mem.busy_lock)),
                )
            )
            return mem
        finally:
            _mem.set_raw(raw)

    def set_memory(self, mem):
        _mem = self._memobj.memory[mem.number - 1]
        if mem.empty:
            _mem.set_raw(b"\xFF" * 48)
            return

        _mem.rxfreq = mem.freq / 10
        if int(_mem.rx_unkw) == 0xFF:
            _mem.rx_unkw = 0x35
            _mem.tx_unkw = 0x32

        if mem.duplex == "+":
            _mem.txfreq = (mem.freq + mem.offset) / 10
        elif mem.duplex == "-":
            _mem.txfreq = (mem.freq - mem.offset) / 10
        elif mem.duplex == "off":
            for byte in _mem.txfreq:
                byte.set_raw(b"\xFF")
        else:
            _mem.txfreq = mem.freq / 10

        ((txmode, txtone, txpol), (rxmode, rxtone, rxpol)) = (
            chirp_common.split_tone_encode(mem)
        )
        self._encode_tone(_mem.tx_tone, txmode, txtone, txpol)
        self._encode_tone(_mem.rx_tone, rxmode, rxtone, rxpol)

        name_length = self.get_features().valid_name_length
        for index in range(name_length):
            try:
                _mem.name[index] = mem.name[index]
            except IndexError:
                _mem.name[index] = "\x20"

        _mem.power = tk760g.POWER_LEVELS.index(
            mem.power or tk760g.POWER_LEVELS[0]
        )
        _mem.wide = tk760g.MODES.index(mem.mode)
        self._set_scan(mem.number - 1, mem.skip)

        if int(_mem.bnumb) == 0xFF:
            _mem.bnumb = mem.number - 1
            _mem.bank = 1

        bank = _extra_integer(mem, "bank")
        if bank is not None:
            _mem.bank = bank
        bank_index = _extra_integer(mem, "bnumb")
        if bank_index is not None:
            _mem.bnumb = bank_index

        for setting in mem.extra:
            if setting.get_name() in _BANK_SETTINGS:
                continue
            setattr(
                _mem,
                setting.get_name(),
                not bool(setting.value),
            )

        # Other channels may still hold erased bank sentinels (bnumb 0x80 or
        # 0xFF) from the radio; get_memory already shows them normalized, so
        # normalize them here too before the bank tables are rebuilt.
        self._normalize_invalid_bank_metadata()
        self._prep_data()
        self._validate_bank_state()
        return mem

    def _write_frame_with_retry(self, frame, address):
        for attempt in range(1, WRITE_ACK_RETRIES + 1):
            tk760g._raw_send(self, frame)
            ack = tk760g._raw_recv(self, 1)
            if ack == tk760g.ACK_CMD:
                return
            if ack == b"\x15" and attempt < WRITE_ACK_RETRIES:
                continue
            tk760g._close_radio(self)
            if ack == b"\x15":
                raise errors.RadioError(
                    "Bad checksum in block %02x write after %i attempts"
                    % (address, attempt)
                )
            if not ack:
                raise errors.RadioNoResponse(
                    "No acknowledgement for block %02x write" % address
                )
            raise errors.RadioError(
                "Problem with the ack to block %02x write, ack %03i"
                % (address, int(ack))
            )

    def sync_out(self):
        self._fill(0xBB, b"Chirp")
        if self._memobj is None:
            self.process_mmap()
        self._normalize_invalid_bank_metadata()
        self._prep_data()
        self._validate_bank_state()

        status = chirp_common.Status()
        tk760g._open_radio(self, status)
        status.cur = 0
        status.max = tk760g.MEM_SIZE // tk760g.BLOCK_SIZE
        status.msg = "Cloning to radio..."
        self.status_fn(status)

        count = 0
        raddr = 0
        for address in tk760g.MEM_BLOCKS:
            data = self.get_mmap()[raddr:raddr + tk760g.BLOCK_SIZE]
            if address in self.RO_BLOCKS:
                if (
                    address >= 0x10
                    and address <= 0x1F
                    and data == tk760g.EMPTY_BLOCK
                ):
                    count += 1
                    raddr = count * tk760g.BLOCK_SIZE
                    continue
                count += 1
                raddr = count * tk760g.BLOCK_SIZE
                continue

            if data == tk760g.EMPTY_BLOCK:
                frame = tk760g._make_frame(b"Z", address) + b"\xFF"
            else:
                checksum = tk760g.checksum.checksum_8bit(data)
                frame = (
                    tk760g._make_frame(b"W", address)
                    + data
                    + bytes([checksum])
                )
            self._write_frame_with_retry(frame, address)

            status.cur = count
            self.status_fn(status)
            count += 1
            raddr = count * tk760g.BLOCK_SIZE

        tk760g._close_radio(self)

    def _normalize_invalid_bank_metadata(self):
        """Replace erased bank sentinels before rebuilding the bank tables."""
        for number, channel in enumerate(self._memobj.memory, start=1):
            if channel.rxfreq[0].get_raw(asbytes=True) == b"\xFF":
                continue
            bank, bank_index = _normalized_bank_metadata(channel, number)
            channel.bank = bank
            channel.bnumb = bank_index

    def _validate_bank_state(self):
        active = []
        for number, channel in enumerate(self._memobj.memory, start=1):
            if channel.rxfreq[0].get_raw(asbytes=True) == b"\xFF":
                continue
            bank = int(channel.bank)
            bank_index = int(channel.bnumb)
            if not 1 <= bank <= 128 or not 0 <= bank_index <= 127:
                raise errors.InvalidValueError(
                    "TK-270G channel %i has invalid bank metadata "
                    "(bank=%i, index=%i); upload stopped before radio I/O"
                    % (number, bank, bank_index)
                )
            active.append((number, bank))

        expected_channels = len(active)
        expected_banks = len({bank for _number, bank in active})
        actual_channels = int(self._memobj.settings.channels)
        actual_banks = int(self._memobj.settings.banks)
        if (
            actual_channels != expected_channels
            or actual_banks != expected_banks
        ):
            raise errors.InvalidValueError(
                "TK-270G bank table validation failed: expected %i channels "
                "in %i banks, generated %i channels in %i banks; upload "
                "stopped before radio I/O"
                % (
                    expected_channels,
                    expected_banks,
                    actual_channels,
                    actual_banks,
                )
            )
