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
        self.noise_x = noise_x
        self.noise_y = noise_y
        self.zero_outside_yag = zero_outside_yag
        super().__init__(prefix, **kwargs)

    @property
    def image(self):
        """
        Returns a blank image using the correct shape of the camera.
        """
        return np.zeros((self.cam.size.size_y.value, 
                         self.cam.size.size_x.value), dtype=np.uint8)

    @property
    def centroid_x(self, **kwargs):
        """
        Returns the beam centroid in x.
        """
        self.check_camera()
        # Override _cent_x with centroid calculator
        self._cent_x(**kwargs)
        # Make sure centroid is an int
        cent_x = int(np.round(self.stats2.centroid.x.value + \
          np.random.uniform(-1,1) * self.noise_x))
        # Check we arent out of bounds
        if self.zero_outside_yag and self._centroid_out_of_bounds():
            cent_x = 0
        return cent_x

    @property
    def centroid_y(self, **kwargs):
        """
        Returns the beam centroid in y.
        """
        self.check_camera()
        # Override _cent_y with centroid calculator
        self._cent_y(**kwargs)
        # Make sure centroid is an int
        cent_y = int(np.round(self.stats2.centroid.y.value + \
          np.random.uniform(-1,1) * self.noise_y))
        # Check we arent out of bounds
        if self.zero_outside_yag and self._centroid_out_of_bounds():
            cent_y = 0
        return cent_y
          
    def _centroid_out_of_bounds(self):
        """
        Checks if the centroid is outside the edges of the yag.
        """
        if ((0 <= self.stats2.centroid.y.value <= self.image.shape[0]) and 
            (0 <= self.stats2.centroid.x.value <= self.image.shape[1])):
            return False
        return True

    def _cent_x(self, **kwargs):
        """
        Place holder method that is can be overriden to calculate the centroid.
        
        Make sure at the end to include a put to the correct centroid field like
        so:
            self.stats2.centroid.x.put(new_cent_calc_x)
        """
        pass
    
    def _cent_y(self, **kwargs):
        """
        Place holder method that is can be overriden to calculate the centroid.
        
        Make sure at the end to include a put to the correct centroid field like
        so:
            self.stats2.centroid.x.put(new_cent_calc_y)
        """
        pass
    

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


