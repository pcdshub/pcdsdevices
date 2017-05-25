#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define the YAG screens used at LCLS.
"""
import logging
from ophyd.utils import enum
from threading import Event, RLock

from .device import Device
from .imsmotor import ImsMotor
from .iocdevice import IocDevice
from .areadetector.detectors import OpalDetector
from .signal import EpicsSignalRO
from ..component import Component

logger = logging.getLogger(__name__)


class FEEYag(Device):
    """
    YAG detector using Dehongs IOC.
    """
    def __init__(self, prefix, *, ioc="", pos_prefix="", read_attrs=None, 
                 name=None, **kwargs):
        imager  = Component(OpalDetector, prefix=prefix, name="Opal Camera")
        zoom = Component(ImsMotor, prefix=prefix+":CLZ:01", ioc=ioc,
                         name="Zoom Motor")
        focus = Component(ImsMotor, prefix=prefix+":CLF:01", ioc=ioc,
                         name="Focus Motor")
        yag = Component(ImsMotor, prefix=prefix+":MOTR", ioc=ioc,
                         name="Yag Motor")
        position = Component(EpicsSignalRO, ":POSITION", add_prefix=pos_prefix)
        
        if read_attrs is None:
            read_attrs = ['imager', 'zoom', 'focus', 'yag', 'position']
        super().__init__(prefix, read_attrs=read_attrs, name=name,
                         **kwargs)
    
