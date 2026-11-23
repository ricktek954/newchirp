# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""DM-32UV override with bounded retries for the password-state query."""

import logging
import time

from chirp import chirp_common, directory, errors
from chirp.drivers import baofeng_dm32uv


LOG = logging.getLogger(__name__)
AIRBAND = (108_000_000, 136_000_000)

_current_xfer = baofeng_dm32uv._Link.xfer
_original_xfer = getattr(_current_xfer, "newchirp_original", _current_xfer)
_current_query_v = baofeng_dm32uv._Link.query_v
_original_query_v = getattr(
    _current_query_v,
    "newchirp_original",
    _current_query_v,
)
_current_construct = baofeng_dm32uv._Link.__init__
_original_construct = getattr(
    _current_construct,
    "newchirp_original",
    _current_construct,
)


def _link_init_with_fixed_timeout(self, pipe):
    _original_construct(self, pipe)
    # FTDI adapters on Windows can misbehave when timeout is changed before
    # every read. Use one short platform-supported timeout and enforce the
    # command deadline in recv() instead.
    self.pipe.timeout = 0.05


def _recv_with_deadline(self, length, timeout=0.5):
    deadline = time.monotonic() + timeout
    response = bytearray()
    while len(response) < length:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        chunk = self.pipe.read(length - len(response))
        if chunk:
            response.extend(chunk)
    return bytes(response)


def _xfer_with_passsta_retry(self, data, length, timeout=0.5):
    if data == b"SYSINFO" and length == 1:
        last_reply = b""
        last_error = None
        for attempt in range(3):
            try:
                response = _original_xfer(self, data, length, timeout)
            except errors.RadioError as exc:
                last_error = exc
            else:
                if response == b"\x06":
                    return response
                last_reply = response
            if attempt < 2:
                time.sleep(0.08)

        detail = (
            "reply %s" % last_reply.hex()
            if last_reply
            else str(last_error or "no reply")
        )
        raise errors.RadioError(
            "Unexpected reply to SYSINFO after 3 attempts (%s). "
            "Power-cycle the radio, reconnect the programming cable, close "
            "the Baofeng CPS, and try the read again." % detail
        )

    if data != b"PASSSTA" or length != 3:
        return _original_xfer(self, data, length, timeout)

    last_reply = b""
    last_error = None
    for attempt in range(3):
        try:
            response = _original_xfer(self, data, length, timeout)
        except errors.RadioError as exc:
            last_error = exc
        else:
            if response and response[0] == ord("P"):
                return response
            last_reply = response
        if attempt < 2:
            time.sleep(0.08)

    if last_reply and last_reply[0] & 0x7F == ord("P"):
        raise baofeng_dm32uv._garbled(
            "Garbled password-state reply from the DM-32UV"
        )
    detail = (
        "reply %s" % last_reply.hex()
        if last_reply
        else str(last_error or "no reply")
    )
    raise errors.RadioError(
        "Unexpected reply to PASSSTA after 3 attempts (%s). Power-cycle the "
        "radio, reconnect the programming cable, close the Baofeng CPS, and "
        "try the read again." % detail
    )


def _query_v_with_retry(self, cmd):
    """Retry read-only radio information queries with slower fragmentation."""
    last_header = b""
    last_body = b""

    for attempt in range(3):
        self.send(cmd)
        header = self.recv(3, timeout=1.5)
        body = (
            self.recv(header[2], timeout=2.0)
            if len(header) == 3
            else b""
        )
        if (
            len(header) == 3
            and header[0] == 0x56
            and len(body) == header[2]
        ):
            return body
        last_header = header
        last_body = body
        if attempt < 2:
            time.sleep(0.08)

    message = (
        "Bad reply to radio info query %s after 3 attempts "
        "(header %s, body %i bytes)"
        % (cmd.hex(), last_header.hex() or "empty", len(last_body))
    )
    raise baofeng_dm32uv._bad_reply(
        message,
        last_header[:1],
        b"V",
    )


_xfer_with_passsta_retry.newchirp_passsta_retry = True
_xfer_with_passsta_retry.newchirp_original = _original_xfer
_query_v_with_retry.newchirp_query_retry = True
_query_v_with_retry.newchirp_original = _original_query_v
_link_init_with_fixed_timeout.newchirp_fixed_timeout = True
_link_init_with_fixed_timeout.newchirp_original = _original_construct
_recv_with_deadline.newchirp_deadline_read = True
if not getattr(baofeng_dm32uv._Link.__init__, "newchirp_fixed_timeout", False):
    baofeng_dm32uv._Link.__init__ = _link_init_with_fixed_timeout
if not getattr(baofeng_dm32uv._Link.recv, "newchirp_deadline_read", False):
    baofeng_dm32uv._Link.recv = _recv_with_deadline
if not getattr(
    baofeng_dm32uv._Link.xfer,
    "newchirp_passsta_retry",
    False,
):
    baofeng_dm32uv._Link.xfer = _xfer_with_passsta_retry
if not getattr(
    baofeng_dm32uv._Link.query_v,
    "newchirp_query_retry",
    False,
):
    baofeng_dm32uv._Link.query_v = _query_v_with_retry


# Upload progress. Stock do_upload reports once per memory tag and only
# relabels "Scanning flash pages" after the first page has been erased and
# written, so the dialog sat on a low percentage for most of a ~50-60 s
# write. A 2026-11-21 owner cancelled two writes at 14 s and 37 s that were
# still working (ledger w-20261121-ab4d). These wrappers relabel the moment
# scanning ends and report every page write. Downloads are unchanged.
WRITE_LABEL = (
    "Writing to radio - this takes about a minute. Keep the cable connected "
    "and do not cancel"
)
_upload_progress = {}
_current_scan = baofeng_dm32uv._scan
_original_scan = getattr(_current_scan, "newchirp_original", _current_scan)
_current_write_page = baofeng_dm32uv._write_page
_original_write_page = getattr(
    _current_write_page, "newchirp_original", _current_write_page
)


def _scan_then_announce_write(link, start, end, radio, status):
    result = _original_scan(link, start, end, radio, status)
    if _upload_progress.get("radio") is radio:
        _upload_progress.update(status=status, pages=0)
        status.msg = WRITE_LABEL
        radio.status_fn(status)
    return result


def _write_page_with_progress(link, addr, data, start, end):
    progress = _upload_progress
    if progress.get("status") is not None:
        progress["pages"] += 1
        status = progress["status"]
        status.msg = "%s (memory page %i)" % (WRITE_LABEL, progress["pages"])
        progress["radio"].status_fn(status)
    return _original_write_page(link, addr, data, start, end)


_scan_then_announce_write.newchirp_original = _original_scan
_write_page_with_progress.newchirp_original = _original_write_page
baofeng_dm32uv._scan = _scan_then_announce_write
baofeng_dm32uv._write_page = _write_page_with_progress


def _tone_value_readable(value):
    """True for no tone, a BCD CTCSS tone CHIRP knows, or a BCD DCS code."""
    if value in (0xFFFF, 0x0000):
        return True
    if value & 0x8000:
        digits = "%03x" % (value & 0x07FF)
        return digits.isdigit() and int(digits) in chirp_common.DTCS_CODES
    digits = "%04x" % (value & 0x7FFF)
    return digits.isdigit() and int(digits) / 10.0 in chirp_common.TONES


def _unreadable_tones(_mem):
    if int(_mem.chtype) in (1, 3):
        return []   # DMR channels: the stock driver never decodes tones
    return [name for name in ("rxtone", "txtone")
            if not _tone_value_readable(int(getattr(_mem, name)))]


def _stored_name(raw):
    """A name as the radio shows it: text up to the first NUL or 0xFF.

    Names written by other software can keep old bytes after the NUL that
    ends them, such as "Channel 1\\x00t Mode" or "RPT 15\\x00 23". The radio
    stops at the NUL; stock CHIRP only stripped trailing padding and showed
    the leftover text (forum file drop 12, 2026-11-20).
    """
    return str(raw).split("\x00")[0].split("\xff")[0].rstrip(" ")


def _zone_get_name(self):
    name = _stored_name(self._zone().name)
    if self.index + 1 > self._model._radio._zone_count() and (
            not name or not name.isprintable()):
        return "New zone"
    return name


_zone_get_name.newchirp_stored_name = True
if not getattr(
    baofeng_dm32uv.DM32UVZone.get_name,
    "newchirp_stored_name",
    False,
):
    baofeng_dm32uv.DM32UVZone.get_name = _zone_get_name


directory.enable_reregistrations()


@directory.register
class DM32UV(baofeng_dm32uv.DM32UV):
    """Baofeng DM-32UV with a retry-safe password-state handshake."""

    def get_features(self):
        features = super().get_features()
        features.valid_bands.insert(0, AIRBAND)
        return features

    def sync_out(self):
        _upload_progress.clear()
        _upload_progress["radio"] = self
        try:
            return super().sync_out()
        finally:
            _upload_progress.clear()

    def get_memory(self, number):
        _mem = self._chan(number)
        bad = _unreadable_tones(_mem)
        if not bad:
            mem = super().get_memory(number)
        else:
            # 2026-11-22 report (firmware DM32.00.01.048): a tone stored as
            # 0x3E08 is neither BCD CTCSS nor DCS, and the stock decoder
            # turned "3e08" into 3e8 Hz, failing the whole read. Show such a
            # tone as none; set_memory puts the raw value back unless the
            # user sets a new tone. The encoding stays unguessed until an
            # image from that firmware is seen (ledger w-20261121-ab4d area,
            # INBOX:907).
            saved = {name: int(getattr(_mem, name)) for name in bad}
            for name in bad:
                setattr(_mem, name, 0xFFFF)
            try:
                mem = super().get_memory(number)
            finally:
                for name, value in saved.items():
                    setattr(_mem, name, value)
            LOG.warning(
                "DM-32UV channel %i: unreadable tone value(s) %s shown as "
                "none and kept unchanged", number,
                ", ".join("%s=0x%04X" % item for item in saved.items()))
        if not mem.empty:
            mem.name = _stored_name(self._chan(number).name)
        return mem

    def set_memory(self, mem):
        _mem = self._chan(mem.number) if not mem.empty else None
        kept = {}
        if _mem is not None and mem.tmode == "":
            kept = {name: int(getattr(_mem, name))
                    for name in _unreadable_tones(_mem)}
        result = super().set_memory(mem)
        for name, value in kept.items():
            setattr(self._chan(mem.number), name, value)
        return result

    def _channel_names(self):
        names = {}
        for number in super()._channel_names():
            names[number] = baofeng_dm32uv._shown(
                _stored_name(self._chan(number).name)
            )
        return names

    def validate_memory(self, memory):
        messages = []
        if (
            AIRBAND[0] <= memory.freq < AIRBAND[1]
            and memory.duplex != "off"
        ):
            messages.append(chirp_common.ValidationError(
                "DM-32UV airband memories must be set to receive-only"
            ))
        return messages + super().validate_memory(memory)

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Switch the DM-32UV on and connect its programming cable at "
            "115200 baud. Close the Baofeng CPS before reading or writing."
        )
        return prompts

