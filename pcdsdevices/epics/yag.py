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
from .areadetector.detectors import FEEOpalDetector
from .signal import EpicsSignalRO
from .component import FormattedComponent

logger = logging.getLogger(__name__)


class FEEYag(Device):
    """
    YAG detector using Dehongs IOC.
    """
    # Opal
    imager  = FormattedComponent(FEEOpalDetector, prefix="{self._prefix}:", 
                                 name="Opal Camera")

    # Yag Motors
    zoom = FormattedComponent(ImsMotor, prefix="{self._prefix}:CLZ:01", 
                              ioc="{self._ioc}", name="Zoom Motor")
    focus = FormattedComponent(ImsMotor, prefix="{self._prefix}:CLF:01", 
                               ioc="{self._ioc}", name="Focus Motor")
    yag = FormattedComponent(ImsMotor, prefix="{self._prefix}:MOTR", 
                             ioc="{self._ioc}", name="Yag Motor")
    
    # Position PV
    pos = FormattedComponent(EpicsSignalRO, "{self._prefix}:POSITION", 
                             add_prefix="{self._pos_pref}")

    def __init__(self, prefix, *, ioc="", pos_pref="", read_attrs=None, 
                 name=None, **kwargs):        
        self._prefix = prefix
        self._pos_pref = pos_pref
        self._ioc = ioc
        if read_attrs is None:
            read_attrs = ['imager', 'zoom', 'focus', 'yag', 'pos']
        super().__init__(prefix, read_attrs=read_attrs, name=name,
                         **kwargs)
    
