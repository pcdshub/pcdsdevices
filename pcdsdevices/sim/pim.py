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

    def __init__(self, prefix, pos_in=0, pos_diode=0.5, pos_out=1, fake_sleep=0,
                 noise=0, **kwargs):
        if pos_diode < pos_in:
            pos_diode = pos_in + 0.5
        if pos_out < pos_diode:
            t_out = t_out + 0.5
        self.pos_d = {"DIODE":pos_diode, "OUT":pos_out, 
                      "IN":pos_in, "YAG":pos_in}
        self.fake_sleep = fake_sleep
        self.noise = noise
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

    @property
    def pos(self):
        return self.pos_d[self.position]+np.random.uniform(-1,1)*self.noise


class PIM(pim.PIM, PIMMotor):
    detector = FormattedComponent(PIMPulnixDetector, 
                                  "{self._section}:{self._imager}:CVV:01",
                                  read_attrs=['stats2'])
    def __init__(self, prefix, x=0, y=0, z=0, noise_x=0, noise_y=0, noise_z=0, 
                 fake_sleep_y=0, **kwargs):
        if len(prefix.split(":")) < 2:
            prefix = "TST:{0}".format(prefix)
        self._x = x
        self._z = z
        super().__init__(prefix, pos_in=y, noise=noise_y, 
                         fake_sleep=fake_sleep_y, **kwargs)

    @property
    def x(self):
        return self._x + np.random.uniform(-1,1)*self.noise_x

    @x.setter
    def x(self, val):
        self._x = val

    @property
    def y(self):
        return self.pos

    @property
    def z(self):
        return self._z + np.random.uniform(-1,1)*self.noise_z

    @z.setter
    def z(self, val):
        self._z = val


