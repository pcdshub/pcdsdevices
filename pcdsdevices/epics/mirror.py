#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .signal import (EpicsSignal, EpicsSignalRO)
from .device import Device
from .imsmotor import ImsMotor
from .component import (FormattedComponent, Component) 


class Mirror(Device):
    """
    Device that steers the beam.
    """
    pitch = FormattedComponent(ImsMotor, "", ioc="{self._ioc}")

    # Currently structured to pass the ioc argument down to the pitch motor
    def __init__(self, prefix, *, name=None, ioc="", read_attrs=None,
                 parent=None, **kwargs):
        self._ioc = ioc
        super().__init__(prefix, name=name, read_attrs=read_attrs,
                         parent=parent, **kwargs)
        interlock = Component(EpicsSignalRO, '.INTERLOCK')
        enabled = Component(EpicsSignalRO, '.ENABLED')

if __name__ is "__main__":
    m = Mirror("TEST:PREF", name='tst', ioc="TEST:IOC")
