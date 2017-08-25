#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Attocube devices
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from .device import Device
from .component import Component
from .epicsmotor import Epicsmotor
from .signal import (EpicsSignal, EpicsSignalRO)

logger = logging.getLogger(__name__)


class EccController(Device):
    """
    ECC Controller
    """
    _firm_day = Component(EpicsSignalRO, ":CALC:FIRMDAY")
    _firm_month = Component(EpicsSignalRO, ":CALC:FIRMMONTH")
    _firm_year = Component(EpicsSignalRO, ":CALC:FIRMYEAR")
    _flash = Component(EpicsSignal, ":RDB:FLASH", write_pv=":CMD:FLASH")
    
    @property 
    def firmware(self):
        """
        Returns the firmware in the same date format as the EDM screen.
        """
        return "{0}/{1}/{2}".format(self._firm_day.value, self._firm_month.value
                                    self._firm_year.value)
    
    @property
    def flash(self):
        """
        Saves the current configuration of the controller.
        """
        return self._flash.set(1)


class EccMotor(EpicsMotor):
    """
    ECC Motor Class
    """
    pass


class TranslationEcc(EccMotor):
    """
    Class for the translation ecc motor
    """
    pass


class GoniometerEcc(EccMotor):
    """
    Class for the goniometer ecc motor
    """
    pass


class DiodeEcc(EccMotor):
    """
    Class for the diode insertion ecc motor
    """
    pass





