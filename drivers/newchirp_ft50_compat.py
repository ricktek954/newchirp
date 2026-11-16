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
