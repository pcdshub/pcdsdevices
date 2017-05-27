#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .iocdevice import IocDevice
from .device import Device
from .component import (Component, FormattedComponent)
from .state import statesrecord_class
from .areadetector.detectors import PulnixDetector

PIMStates = statesrecord_class("PIMStates", ":OUT", ":YAG", ":DIODE")


class PIM(Device):
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

class PIMYag(PIM):
    """
    PIM device that also includes a yag.
    """
    imager = FormattedComponent(PulnixDetector, "{self._imager}", name="Pulnix")

    def __init__(self, prefix, *, ioc="", imager="", configuration_attrs=None,
                 **kwargs):
        self._imager = imager

        if configuration_attrs is None:
            configuration_attrs = ['imager', 'states']
        super().__init__(prefix, configuration_attrs=configuration_attrs, 
                         **kwargs)
