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
    @classmethod
    def detect_from_serial(cls, pipe):
        return TDH3.detect_from_serial(pipe)

    def get_settings(self):
        _sanitize_brightness(self)
        return super().get_settings()


@directory.register
class TDH3_GMRS(tdh8.TDH3_GMRS):
    @classmethod
    def detect_from_serial(cls, pipe):
        return TDH3.detect_from_serial(pipe)

    def get_settings(self):
        _sanitize_brightness(self)
        return super().get_settings()


# Ensure family detection resolves NewChirp's registered classes rather than
# the upstream TD-H3 variants inherited through tdh8. The reporter's radio
# identifies as the generic P31183 variant even when a TIDRADIO HAM or GMRS
# catalog entry was selected.
TDH3.DETECTED_MODELS_TDH3 = [TDH3, TDH3_HAM, TDH3_GMRS]
