#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
import time

###############
# Third Party #
###############
from ophyd.signal import ArrayAttributeSignal

##########
# Module #
##########
from .signal import Signal
from .component import (FormattedComponent, Component)
from .areadetector.plugins import StatsPlugin
from .areadetector.detectors import PulnixDetector
from ..epics import pim


class PIMPulnixDetector(pim.PIMPulnixDetector, PulnixDetector):
    proc1 = Component(Signal)
    image2 = Component(Signal)
    stats1 = Component(StatsPlugin, "Stats1:", read_attrs=['centroid',
                                                            'mean_value'])
    stats2 = Component(StatsPlugin, ":Stats2:", read_attrs=['centroid',
                                                            'mean_value'])
    

class PIMMotor(pim.PIMMotor):
    states = Component(Signal, value="OUT")

    def __init__(self, prefix, fake_sleep=0, y_in=0, y_diode=0.5, y_out=1, 
                 **kwargs):
        self.fake_sleep = fake_sleep
        if y_diode < y_in:
            y_diode = y_in + 0.5
        if y_out < y_diode:
            t_out = t_out + 0.5
        self.y_pos = {"DIODE":y_diode, "OUT":y_out, "IN":y_in, "YAG":y_in}
        super().__init__(prefix, **kwargs)
    
    def move(self, position, **kwargs):
        if isinstance(position, str):
            if position.upper() in ("DIODE", "OUT", "IN", "YAG"): 
                self.states.put("MOVING")
                if position.upper() == "IN":
                    pos = "YAG"
                else:
                    pos = position.upper()
                if self.fake_sleep:
                    time.sleep(self.fake_sleep)
                status = self.states.set(position.upper())
                time.sleep(0.1)
                return status
        raise ValueError("Position must be a PIM valid state.")

    @property
    def position(self):
        pos = self.states.value
        if pos == "YAG":
            return "IN"
        return pos


class PIM(pim.PIM, PIMMotor):
    detector = FormattedComponent(PIMPulnixDetector, 
                                  "{self._section}:{self._imager}:CVV:01",
                                  read_attrs=['stats2'])
    def __init__(self, prefix, x=0, z=0, **kwargs):
        if len(prefix.split(":")) < 2:
            prefix = "TST:{0}".format(prefix)
        self.x = x
        self.z = z
        super().__init__(prefix, **kwargs)
