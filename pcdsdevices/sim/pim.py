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
from .device import SimDevice
from .signal import FakeSignal
from .component import (FormattedComponent, Component)
from .areadetector.plugins import StatsPlugin
from .areadetector.detectors import PulnixDetector
from ..epics import pim


class PIMPulnixDetector(pim.PIMPulnixDetector, PulnixDetector):
    proc1 = Component(FakeSignal)
    image2 = Component(FakeSignal)
    stats1 = Component(StatsPlugin, "Stats1:", read_attrs=['centroid',
                                                            'mean_value'])
    stats2 = Component(StatsPlugin, ":Stats2:", read_attrs=['centroid',
                                                            'mean_value'])

    def __init__(self, prefix, *, noise_x=False, noise_y=False, noise_func=None, 
                 noise_type="norm", noise_args=(), noise_kwargs={}, 
                 zero_outside_yag=True, **kwargs):
        super().__init__(prefix, **kwargs)
        self.noise_x = noise_x
        self.noise_y = noise_y
        self.noise_func = noise_func
        self.noise_type = noise_type
        self.noise_args = noise_args
        self.noise_kwargs = noise_kwargs
        self.zero_outside_yag = zero_outside_yag
        self.stats2._get_readback_centroid_x = lambda **kwargs : (
            self._get_readback_centroid_x() * self._centroid_within_bounds())
        self.stats2._get_readback_centroid_y = lambda **kwargs : (
            self._get_readback_centroid_y() * self._centroid_within_bounds())

    @property
    def image(self):
        """
        Returns a blank image using the correct shape of the camera. Override
        this if you want spoof images.
        """
        return np.zeros((int(self.cam.size.size_y.value), 
                         int(self.cam.size.size_x.value)), dtype=np.uint8)

    @property
    def centroid_x(self, **kwargs):
        """
        Returns the beam centroid in x.
        """
        self.check_camera()
        return self.stats2.centroid.x.value
        
    @property
    def centroid_y(self, **kwargs):
        """
        Returns the beam centroid in y.
        """
        self.check_camera()
        return self.stats2.centroid.y.value
          
    def _centroid_within_bounds(self):
        """
        Checks if the centroid is outside the edges of the yag.
        """
        in_x = 0 <= self.stats2.centroid.x._raw_readback <= self.image.shape[0]
        in_y = 0 <= self.stats2.centroid.y._raw_readback <= self.image.shape[1]
        if not self.zero_outside_yag or (in_x and in_y):
            return True
        return False
    
    def _get_readback_centroid_x(self):
        return self.stats2.centroid.x._raw_readback

    def _get_readback_centroid_y(self):
        return self.stats2.centroid.y._raw_readback

    @property
    def noise_x(self):
        return self.stats2.noise_x

    @noise_x.setter
    def noise_x(self, val):
        self.stats2.noise_x = bool(val)

    @property
    def noise_y(self):
        return self.stats2.noise_y

    @noise_y.setter
    def noise_y(self, val):
        self.stats2.noise_y = bool(val)

    @property
    def noise_func(self):
        return (self.stats2.noise_func_x(), self.stats2.noise_func_y())
        
    @noise_func.setter
    def noise_func(self, val):
        self.stats2.noise_func_x = val
        self.stats2.noise_func_y = val

    @property
    def noise_type(self):
        return (self.stats2.noise_type_x, self.stats2.noise_type_y)

    @noise_type.setter
    def noise_type(self, val):
        self.stats2.noise_type_x = val
        self.stats2.noise_type_y = val

    @property
    def noise_args(self):
        return (self.stats2.noise_args_x, self.stats2.noise_args_y)

    @noise_args.setter
    def noise_args(self, val):
        self.stats2.noise_args_x = val
        self.stats2.noise_args_y = val

    @property
    def noise_kwargs(self):
        return (self.stats2.noise_kwargs_x, self.stats2.noise_kwargs_y)

    @noise_kwargs.setter
    def noise_kwargs(self, val):
        self.stats2.noise_kwargs_x = val
        self.stats2.noise_kwargs_y = val
    

class PIMMotor(pim.PIMMotor):
    states = Component(FakeSignal, value="OUT")

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


class PIM(pim.PIM, PIMMotor, SimDevice):
    detector = FormattedComponent(PIMPulnixDetector, 
                                  "{self._section}:{self._imager}:CVV:01",
                                  read_attrs=['stats2'])
    def __init__(self, prefix, x=0, y=0, z=0, noise_x=0, noise_y=0, noise_z=0, 
                 settle_time_y=0, centroid_noise=(0,0), **kwargs):
        if len(prefix.split(":")) < 2:
            prefix = "TST:{0}".format(prefix)
        super().__init__(prefix, pos_in=y, noise=noise_y, 
                         fake_sleep=fake_sleep_y, **kwargs)
        self.noise_x = noise_x
        self.noise_z = noise_z
        if not isinstance(centroid_noise, (tuple, list)):
            centroid_noise = (centroid_noise, centroid_noise)
        self.detector.noise_x = centroid_noise[0]
        self.detector.noise_y = centroid_noise[1]

        # Simulation values

