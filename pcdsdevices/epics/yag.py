#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define the YAG screens used at LCLS.
"""
import logging

from ophyd.utils import enum

from .device import Device
from .imsmotor import ImsMotor
from .iocdevice import IocDevice
from .signal import EpicsSignalRO
from .component import FormattedComponent
from .areadetector.detectors import FEEOpalDetector

logger = logging.getLogger(__name__)


class FEEYag(Device):
    """
    YAG detector using Dehongs IOC.
    """
    # Opal
    imager = FormattedComponent(FEEOpalDetector, "{self._prefix}", 
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
