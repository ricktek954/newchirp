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

"""Expose the Baofeng UV-29 Pro under its vendor compatibility profile."""

from chirp import directory
from chirp.drivers import baofeng_uv17Pro


@directory.register
class UV29Pro(baofeng_uv17Pro.UV28Plus):
    """Baofeng UV-29 Pro using Baofeng's UV-28 Plus profile."""

    VENDOR = "Baofeng"
    MODEL = "UV-29Pro"
