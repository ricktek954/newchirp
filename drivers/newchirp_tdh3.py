"""TD-H3 settings compatibility for radios with an unset brightness byte."""

from chirp import directory
from chirp.drivers import tdh8


def _sanitize_brightness(radio):
    """Keep 0xFF from becoming an invalid list index in the settings UI."""
    settings = radio._memobj.settings
    if int(settings.brightness) not in range(5):
        # The UI reverses the stored levels. Zero is the brightest setting and
        # guarantees that an unset value does not leave the screen invisible.
        settings.brightness = 0


@directory.register
class TDH3(tdh8.TDH3):
    def get_settings(self):
        _sanitize_brightness(self)
        return super().get_settings()


@directory.register
class TDH3_HAM(tdh8.TDH3_HAM):
    def get_settings(self):
        _sanitize_brightness(self)
        return super().get_settings()


@directory.register
class TDH3_GMRS(tdh8.TDH3_GMRS):
    def get_settings(self):
        _sanitize_brightness(self)
        return super().get_settings()
