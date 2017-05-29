#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from .iocdevice import IocDevice
from .device import Device
from .component import (Component, FormattedComponent)
from .state import statesrecord_class
from .areadetector.detectors import PulnixDetector
from .areadetector.plugins import (ImagePlugin, StatsPlugin)

logger = logging.getLogger(__name__)

PIMStates = statesrecord_class("PIMStates", ":OUT", ":YAG", ":DIODE")


class PIMPulnixDetector(PulnixDetector):
    image2 = Component(ImagePlugin, ":IMAGE2:", read_attrs=['array_data'])
    stats1 = Component(StatsPlugin, ":Stats1:", read_attrs=['centroid'])
    stats2 = Component(StatsPlugin, ":Stats2:", read_attrs=['centroid'])
    

class PIMMotor(Device):
    """
    Standard position monitor. Consists of one stage that can either block the
    beam with a YAG crystal or put a diode in. Has a camera that looks at the
    YAG crystal to determine beam position.
    """
    states = Component(PIMStates, "")

    @property
    def blocking(self):
        if self.states.value in ("OUT", "DIODE"):
            return False
        return True

    def move_in(self):
        """
        Move the PIM to the YAG position.
        """
        self.states.value = "YAG"

    def move_out(self):
        """
        Move the PIM to the OUT position.
        """
        self.states.value = "OUT"

    def move_diode(self):
        """
        Move the PIM to the DIODE position.
        """
        self.states.value = "DIODE"

class PIM(Device):
    """
    PIM device that also includes a yag.
    """
    imager = FormattedComponent(PIMPulnixDetector, "{self._imager}")
    motor = Component(PIMMotor, "")

    def __init__(self, prefix, *, imager="", **kwargs):
        self._imager = imager

        super().__init__(prefix, **kwargs)
