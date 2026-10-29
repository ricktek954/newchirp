# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Icom IC-9700 driver with strict CI-V auto-baud validation."""

import logging

from chirp import directory, errors
from chirp.drivers import icomciv


LOG = logging.getLogger(__name__)

BAUD_RATES = (19200, 115200, 9600, 38400, 57600, 4800)
IC9700_ADDRESS = 0xA2
CONTROLLER_ADDRESS = 0xE0


def _discard_serial_input(pipe):
    for method in ("reset_input_buffer", "flushInput"):
        reset = getattr(pipe, method, None)
        if reset is not None:
            reset()
            return


class StrictIcom9700BaudMixin:
    """Require a valid IC-9700 response before accepting a baud rate."""

    def _detect_baudrate(self):
        if self._baud_detected:
            return

        parent = getattr(self, "_parent", None)
        if parent is not None and getattr(parent, "_baud_detected", False):
            self.pipe.baudrate = parent.pipe.baudrate
            self._willecho = parent._willecho
            self._baud_detected = True
            self.pipe.timeout = 1
            return

        # Never enter this sweep twice, even when every baud rate fails.
        self._baud_detected = True
        original_timeout = self.pipe.timeout
        self.pipe.timeout = 0.25

        for baud in BAUD_RATES:
            self.pipe.baudrate = baud
            _discard_serial_input(self.pipe)
            self._willecho = self._detect_echo()
            try:
                frame = icomciv.IC9700MemFrame()
                frame.set_location(self._template)
                self._send_frame(frame)
                source, destination = frame.read(self.pipe)
                if (
                    source != CONTROLLER_ADDRESS
                    or destination != IC9700_ADDRESS
                    or frame._cmd != 0x1A
                    or frame._sub != 0x00
                ):
                    raise errors.RadioError(
                        "CI-V response did not match an IC-9700 memory read"
                    )
            except Exception:
                continue

            if parent is not None:
                parent.pipe.baudrate = baud
                parent._willecho = self._willecho
                parent._baud_detected = True
            LOG.info("Detected Icom IC-9700 at %i baud", baud)
            self.pipe.timeout = 1
            return

        self.pipe.baudrate = self.BAUD_RATE
        self.pipe.timeout = 1
        LOG.warning(
            "Unable to detect IC-9700 baud rate; using default of %i",
            self.BAUD_RATE,
        )
        raise errors.RadioNoResponse(
            "The IC-9700 did not return a valid CI-V reply at any supported "
            "baud rate. Close Icom RS-BA1 or any other program using the COM "
            "port. On the radio, open SET > Connectors > CI-V: set CI-V "
            "Address to A2h, set CI-V USB Port to Unlink from [REMOTE], set "
            "CI-V USB Baud Rate to 115200, and turn CI-V Transceive off. "
            "Reconnect the USB cable, then read the radio again."
        )


directory.enable_reregistrations()


@directory.register
class Icom9700Radio(
    StrictIcom9700BaudMixin,
    icomciv.Icom9700Radio,
):
    """IC-9700 with validated CI-V connection detection."""

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.info = (
            "Connect the IC-9700 with a USB cable. Close Icom RS-BA1 and any "
            "other program using the radio's COM port. In SET > Connectors > "
            "CI-V, use address A2h, set CI-V USB Port to Unlink from [REMOTE], "
            "set CI-V USB Baud Rate to 115200, and turn CI-V Transceive off."
        )
        prompts.pre_download = (
            "Confirm the IC-9700 CI-V address is A2h, CI-V USB Port is "
            "Unlink from [REMOTE], CI-V USB Baud Rate is 115200, and CI-V "
            "Transceive is off. Reconnect the USB cable after changing "
            "these settings."
        )
        prompts.pre_upload = (
            "Read the radio successfully first and save a backup image. "
            "Keep the IC-9700 powered on and do not change radio menus while "
            "the upload is running."
        )
        return prompts

    def get_sub_devices(self):
        return [
            Icom9700RadioBand(self, 1),
            Icom9700RadioBand(self, 2),
            Icom9700RadioBand(self, 3),
            Icom9700SatelliteBand(self),
        ]


class Icom9700RadioBand(
    StrictIcom9700BaudMixin,
    icomciv.Icom9700RadioBand,
):
    """Band view using the parent's validated CI-V connection."""


class Icom9700SatelliteBand(
    StrictIcom9700BaudMixin,
    icomciv.Icom9700SatelliteBand,
):
    """Satellite view using the parent's validated CI-V connection."""

