#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .device import Device
from .imsmotor import ImsMotor
from .component import FormattedComponent


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
