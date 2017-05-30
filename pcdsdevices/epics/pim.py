#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from .device import Device
from .imsmotor import ImsMotor
from .iocdevice import IocDevice
from .signal import EpicsSignalRO
from .state import statesrecord_class
from .component import (Component, FormattedComponent)
from .areadetector.detectors import (PulnixDetector, FeeOpalDetector)
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
    imager = FormattedComponent(PIMPulnixDetector, "{self._section}:{self._imager}:CVV:01")
    motor = Component(PIMMotor, "")

    def __init__(self, prefix, **kwargs):
        self._section = prefix.split(":")[0]
        self._imager = prefix.split(":")[1]
        super().__init__(prefix, **kwargs)

    
class PIMFee(Device):
    """
    YAG detector using Dehongs IOC.
    """
    # Opal
    imager = FormattedComponent(FeeOpalDetector, "{self._prefix}", 
                                name="Opal Camera")

    # Yag Motors
    zoom = FormattedComponent(ImsMotor, "{self._prefix}:CLZ:01", 
                              ioc="{self._ioc}", name="Zoom Motor")
    focus = FormattedComponent(ImsMotor, "{self._prefix}:CLF:01", 
                               ioc="{self._ioc}", name="Focus Motor")
    yag = FormattedComponent(ImsMotor, "{self._prefix}:MOTR", 
                             ioc="{self._ioc}", name="Yag Motor")
    
    # Position PV
    pos = FormattedComponent(EpicsSignalRO, "{self._pos_pref}:POSITION")

    def __init__(self, prefix, *, pos_pref="", ioc="", read_attrs=None, 
                 name=None, parent=None, configuration_attrs=None, **kwargs):        
        self._prefix = prefix
        self._pos_pref = pos_pref
        self._ioc=ioc

        if read_attrs is None:
            read_attrs = ['imager', 'zoom', 'focus', 'yag', 'pos']

        if configuration_attrs is None:
            configuration_attrs = ['imager', 'zoom', 'focus', 'yag', 'pos']
            
        super().__init__(prefix, read_attrs=read_attrs, name=name, parent=parent,
                         configuration_attrs=configuration_attrs, **kwargs)    

