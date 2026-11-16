# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""IC-7100 mode fallback for empty and undocumented CI-V mode bytes."""

from chirp import directory, errors
from chirp.drivers import icomciv


directory.enable_reregistrations()


def _is_known_mode(index):
    return (
        0 <= int(index) < len(icomciv.IcomCIVRadio._MODES)
        and icomciv.IcomCIVRadio._MODES[int(index)] is not None
    )


class _FallbackModes(list):
    def __init__(self, values):
        super().__init__(values)
        self.last_unknown_index = None

    def __getitem__(self, index):
        self.last_unknown_index = None
        if not _is_known_mode(index):
            self.last_unknown_index = int(index)
            return "FM"
        return super().__getitem__(index)


def _mark_opaque_mode(memory, index):
    memory.mode = "FM"
    if "mode" not in memory.immutable:
        memory.immutable.append("mode")
    note = (
        "Unrecognized CI-V mode byte 0x%02x is preserved; this channel "
        "cannot be uploaded until its mode is supported." % int(index)
    )
    memory.comment = (
        "%s %s" % (memory.comment, note) if memory.comment else note
    )


@directory.register
class NewChirpIcom7100(icomciv.Icom7100Radio):
    """IC-7100 with safe handling for unknown stored mode values."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._MODES = _FallbackModes(icomciv.IcomCIVRadio._MODES)

    @classmethod
    def get_prompts(cls):
        prompts = super().get_prompts()
        prompts.experimental = (
            "NewChirp can display IC-7100 channels that contain undocumented "
            "CI-V mode bytes. Those channels are read-only, and uploads stop "
            "before radio I/O until the unknown mode is supported."
        )
        return prompts

    def get_memory(self, number):
        self._MODES.last_unknown_index = None
        memory = super().get_memory(number)
        unknown_index = self._MODES.last_unknown_index
        if unknown_index is not None:
            _mark_opaque_mode(memory, unknown_index)
        return memory

    def _existing_mode_index(self, number):
        frame = self._classes["mem"]()
        if self._rf.has_bank:
            channel, bank = self.mem_to_ch_bnk(number)
            frame.set_location(channel, bank)
        else:
            frame.set_location(number)
        self._send_frame(frame)
        frame = self._recv_frame(frame)
        data = frame.get_data()
        if not data or data[-1] == 0xFF:
            return None
        return int(frame.get_obj().mode)

    def set_memory(self, memory):
        mode_index = self._existing_mode_index(memory.number)
        if mode_index is not None and not _is_known_mode(mode_index):
            raise errors.InvalidValueError(
                "IC-7100 channel %i contains unsupported CI-V mode 0x%02x. "
                "Upload stopped before radio I/O to preserve it."
                % (memory.number + 1, mode_index)
            )
        return super().set_memory(memory)
