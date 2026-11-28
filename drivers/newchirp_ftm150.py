# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Yaesu FTM-150R/E/ASP experimental driver.

The official ADMS-17 v1.0.1 default image is 98304 bytes with model
identifier AH086. Its channel records and surrounding layout are compatible
with the CHIRP FTM-300DR AH071 driver. NewChirp initially exposes memory
channels only; untested APRS, GPS, and digital settings remain hidden.
"""

from chirp import chirp_common
from chirp import directory
from chirp.drivers import ftm300d


@directory.register
class FTM150Radio(ftm300d.FTM300Radio,
                  chirp_common.ExperimentalRadio):
    """Yaesu FTM-150R/E/ASP."""

    VENDOR = "Yaesu"
    MODEL = "FTM-150R"
    FORMATS = [
        directory.register_format("Yaesu FTM-150 SD ALL", "*.dat"),
    ]

    _model = b"AH086"

    @classmethod
    def get_prompts(cls):
        rp = chirp_common.RadioPrompts()
        rp.experimental = (
            "The FTM-150R/E/ASP driver is experimental. Memory channels use "
            "the AH086 image layout and clone transport shared with the "
            "FTM-300DR family. Keep a complete microSD ALL backup before "
            "every upload. Verify a download first and report any unexpected "
            "channel or radio behavior."
        )
        rp.info = (
            "Use an SCU-56 USB cable or CT-163 serial cable on the DATA jack "
            "at 38400 8N1. On the radio, select CLONE/RESET and then "
            "[59 Other -> This] for download or [58 This -> Other] for upload."
        )
        rp.pre_download = (
            "1. Connect the programming cable to the radio DATA jack.\n"
            "2. Hold the right DIAL knob and choose CLONE/RESET.\n"
            "3. Select [59 Other -> This] and confirm with OK.\n"
            "4. Start the download when the radio is waiting."
        )
        rp.pre_upload = (
            "Keep a complete microSD ALL backup before writing.\n"
            "1. Connect the programming cable to the radio DATA jack.\n"
            "2. Hold the right DIAL knob and choose CLONE/RESET.\n"
            "3. Select [58 This -> Other] and confirm with OK.\n"
            "4. Start the upload when the radio is waiting."
        )
        return rp

    def get_features(self):
        rf = super().get_features()
        rf.has_settings = False
        rf.valid_modes = ["FM", "NFM", "AM"]
        rf.valid_bands = [
            (108000000, 174000000),
            (174000000, 400000000),
            (400000000, 550000000),
        ]
        return rf

    def get_settings(self):
        from chirp.settings import RadioSettings

        return RadioSettings()

    def set_settings(self, settings):
        return None



@directory.register
class FTM150ERadio(FTM150Radio):
    """Yaesu FTM-150E: the same AH086 radio as the FTM-150R.

    Registered under upstream CHIRP's Yaesu_FTM-150E driver ID so that
    NewChirp's driver is used for it on every CHIRP pin.
    """

    MODEL = "FTM-150E"
