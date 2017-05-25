#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define the YAG screens used at LCLS.
"""
import logging
from ophyd.enum import Enum
from threading import Event, RLock

from .device import Device
from .imsmotor import ImsMotor
from .iocdevice import IocDevice
from .areadetector.detectors import OpalDetector
from ..component import Component

logger = logging.getLogger(__name__)


class FEEYag(OpalDetector, IocDevice):
    """
    YAG detector using Dehongs IOC.
    """
    def __init__(self, prefix, *, ioc="", motor_ioc="", pos="", read_attrs=None, 
                 name=None, **kwargs):
        zoom = Component(ImsMotor, prefix=prefix+":CLZ:01", ioc=motor_ioc,
                         name="Zoom Motor")
        focus = Component(ImsMotor, prefix=prefix+":CLF:01", ioc=motor_ioc,
                         name="Focus Motor")
        yag = Component(ImsMotor, prefix=prefix+":MOTR", ioc=motor_ioc,
                         name="Yag Motor")
        position = Component(EpicsSignalRO, ":POSITION")
        
        if read_attrs is None:
            read_attrs = ['zoom', 'focus', 'yag', 'position', 'array_data']
        super().__init__(prefix, ioc=ioc, read_attrs=read_attrs, name=name,
                         **kwargs)
    
