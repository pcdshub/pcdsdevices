#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
import time

###############
# Third Party #
###############
import numpy as np
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

    def __init__(self, prefix, *, noise_x=0, noise_y=0, zero_outside_yag=False,
                 **kwargs):
        self.zero_outside_yag = zero_outside_yag
        super().__init__(prefix, **kwargs)
        # Override the lower level centroid read 
        self.stats2.noise_x = noise_x
        self.stats2.noise_y = noise_y
        self.stats2.zero_outside_yag = zero_outside_yag
        self.stats2._centroid_out_of_bounds = self._centroid_out_of_bounds

    @property
    def image(self):
        """
        Returns a blank image using the correct shape of the camera. Override
        this if you want spoof images.
        """
        return np.zeros((self.cam.size.size_y.value, 
                         self.cam.size.size_x.value), dtype=np.uint8)

    @property
    def centroid_x(self, **kwargs):
        """
        Returns the beam centroid in x.
        """
        self.check_camera()
        read = self.stats2.read()
        return read["{0}_centroid_x".format(self.stats2.name)]['value']
        
    @property
    def centroid_y(self, **kwargs):
        """
        Returns the beam centroid in y.
        """
        self.check_camera()
        read = self.stats2.read()
        return read["{0}_centroid_y".format(self.stats2.name)]['value']
          
    def _centroid_out_of_bounds(self):
        """
        Checks if the centroid is outside the edges of the yag.
        """
        if ((0 <= self.stats2.centroid.y.value <= self.image.shape[0]) and 
            (0 <= self.stats2.centroid.x.value <= self.image.shape[1])):
            return False
        return True
    

class PIMMotor(pim.PIMMotor):
    states = Component(Signal, value="OUT")

    def __init__(self, prefix, pos_in=0, pos_diode=0.5, pos_out=1, fake_sleep=0,
                 noise=0, **kwargs):
        if pos_diode < pos_in:
            pos_diode = pos_in + 0.5
        if pos_out < pos_diode:
            pos_out = pos_diode + 0.5
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
                 fake_sleep_y=0, centroid_noise=(0,0), **kwargs):
        if len(prefix.split(":")) < 2:
            prefix = "TST:{0}".format(prefix)
        self.i_x = x
        self.i_z = z
        self.noise_x = noise_x
        self.noise_z = noise_z
        super().__init__(prefix, pos_in=y, noise=noise_y, 
                         fake_sleep=fake_sleep_y, **kwargs)
        if not isinstance(centroid_noise, (tuple, list)):
            centroid_noise = (centroid_noise, centroid_noise)
        self.detector.noise_x = centroid_noise[0]
        self.detector.noise_y = centroid_noise[1]

    @property
    def _x(self):
        return self.i_x + np.random.uniform(-1,1)*self.noise_x

    @_x.setter
    def _x(self, val):
        self.i_x = val

    @property
    def _y(self):
        return self.pos

    @property
    def _z(self):
        return self.i_z + np.random.uniform(-1,1)*self.noise_z

    @_z.setter
    def _z(self, val):
        self.i_z = val


