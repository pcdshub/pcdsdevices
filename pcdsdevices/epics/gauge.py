#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gauge Classes
"""

############
# Standard #
############
import logging

###############
# Third Party #
###############
import numpy as np
from ophyd.utils.epics_pvs import raise_if_disconnected

##########
# Module #
##########
from .device import Device
from .signal import (EpicsSignal, EpicsSignalRO)
from .component import (Component, FormattedComponent)

logger = getLogger(__name__)


class GaugeBase(Device):
    """
    
    """
    pressure = Component(EpicsSignalRO, ":P", auto_monitor=True)
    status = Component(EpicsSignalRO, ":STATE")

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None. **kwargs):
        if read_attrs is None:
            read_attrs = ['pressure, status']
        if configuration_attrs is None:
            configuration_attrs = ['pressure, status']
        
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, name=name, 
                         parent=parent, **kwargs)
    
    @property
    def p(self):
        """
        Pressure readback.
        """
        return pressure.get()

class Pirani(GaugeBase):
    """
    Basic pirani gauge with pressure and status readbacks.
    """
    pass


class ColdCathode(GaugeBase):
    """
    Basic cold cathode gauge with pressure and status readbacks.
    """
    pirani = FormattedComponent(Pirani, "self._prefix_pirani")
    
    def __init__(self, prefix, *, prefix_pirani=None, read_attrs=None, 
                 configuration_attrs=None, name=None, parent=None. **kwargs):
        # Infer the paired pirani from the CC prefix otherwise use input
        if prefix_pirani is None:
            self._prefix_pirani = prefix.replace("VGCC", "VGCP")
        else:
            self._prefix_pirani = prefix_pirani
        
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, name=name, 
                         parent=parent, **kwargs)



