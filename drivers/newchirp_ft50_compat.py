# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Decode odd-split channels stored by Yaesu FT-50 radios."""

from chirp.drivers import ft50


# The OEM ADMS-1E programmer configures COM1 with "9600,n,8,2" before
# entering clone mode. CHIRP's stock driver only declares the baud rate, so
# NewChirp's bridge would otherwise use its pyserial default of one stop bit.
ft50.FT50Radio.SERIAL_STOPBITS = 2

_ORIGINAL_GET_FEATURES = ft50.FT50Radio.get_features


def _get_features(self):
    features = _ORIGINAL_GET_FEATURES(self)
    features.valid_duplexes = list(ft50.DUPLEX)
    features.can_odd_split = True
    return features


_get_features.newchirp_ft50_odd_split = True


if "split" not in ft50.DUPLEX:
    ft50.DUPLEX.append("split")

if not getattr(
    ft50.FT50Radio.get_features,
    "newchirp_ft50_odd_split",
    False,
):
    ft50.FT50Radio.get_features = _get_features


# Clearing a channel must produce a real empty slot.
#
# The FT-50 stores every channel's flag byte twice: flag[] at 0x001A and
# flag_repeat[] at 0x079C. In the CHIRP reference dump from a physical radio
# (tests/images/Yaesu_FT-50.img) both tables are identical: empty channels are
# 0x00 and the in-use channel is 0x03 (used + mask). Stock set_memory clears
# only flag[].used and returns before its copy to flag_repeat[], so a cleared
# channel was uploaded as flag 0x02 / repeat 0x03 and stayed on the radio.
# (2026-11-18 user report: blanked channels survived a write.)
_ORIGINAL_SET_MEMORY = ft50.FT50Radio.set_memory


def _set_memory(self, mem):
    if not mem.empty:
        return _ORIGINAL_SET_MEMORY(self, mem)
    for table in (self._memobj.flag, self._memobj.flag_repeat):
        flag = table[mem.number - 1]
        flag.used = False
        flag.mask = False
        flag.skip = 0
    return None


_set_memory.newchirp_ft50_clears_both_flag_tables = True

if not getattr(
    ft50.FT50Radio.set_memory,
    "newchirp_ft50_clears_both_flag_tables",
    False,
):
    ft50.FT50Radio.set_memory = _set_memory
