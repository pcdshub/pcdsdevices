#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Profile intensity monitor classes and components.
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
import numpy as np
from ophyd.utils.epics_pvs import (raise_if_disconnected, AlarmSeverity)

##########
# Module #
##########
from .device import Device
from .imsmotor import ImsMotor
from .iocdevice import IocDevice
from .state import statesrecord_class
from .signal import (EpicsSignal, EpicsSignalRO)
from .component import (Component, FormattedComponent)
from .areadetector.detectors import (PulnixDetector, FeeOpalDetector)
from .areadetector.plugins import (ImagePlugin, StatsPlugin, ProcessPlugin)
from ..utils.pyutils import isnumber

logger = logging.getLogger(__name__)

PIMStates = statesrecord_class("PIMStates", ":OUT", ":YAG", ":DIODE")


class PIMPulnixDetector(PulnixDetector):
    """
    Pulnix detector that is used in the PIM. Plugins should be added on an as
    needed basis here.
    """
    proc1 = Component(ProcessPlugin, ":Proc1:", read_attrs=['num_filter'])
    image1 = Component(ImagePlugin, ":IMAGE1:", read_attrs=['array_data'])
    image2 = Component(ImagePlugin, ":IMAGE2:", read_attrs=['array_data'])
    stats1 = Component(StatsPlugin, ":Stats1:", read_attrs=['centroid',
                                                            'mean_value'])
    stats2 = Component(StatsPlugin, ":Stats2:", read_attrs=['centroid',
                                                            'mean_value'])

    def check_camera(self):
        """
        Checks if the camera is acquiring images.
        """
        if not self.acquiring:
            raise NotAcquiringError

    @property
    @raise_if_disconnected
    def image(self):
        """
        Returns the image stream reshaped to be the correct size using the size
        component in cam.
        """
        return np.reshape(np.array(self.image2.array_data.value),
                          (self.cam.size.size_y.value,
                           self.cam.size.size_x.value))

    @property
    @raise_if_disconnected
    def acquiring(self):
        """
        Checks to see if the camera is currently acquiring iamges.
        """
        return bool(self.cam.acquire.value)

    @acquiring.setter
    def acquiring(self, val):
        """
        Setter for acquiring.
        """
        return self.cam.acquire.set(bool(val))

    @property
    @raise_if_disconnected
    def centroid_x(self):
        """
        Returns the beam centroid in x.
        """
        self.check_camera()
        return self.stats2.centroid.x.value

    @property
    @raise_if_disconnected
    def centroid_y(self):
        """
        Returns the beam centroid in y.
        """
        self.check_camera()
        return self.stats2.centroid.y.value

    @property
    def centroid(self):
        """
        Returns the beam centroid in y.
        """
        return (self.centroid_x, self.centroid_y)
        

class PIMMotor(Device):
    """
    Standard position monitor. Consists of one stage that can either block the
    beam with a YAG crystal or put a diode in. Has a camera that looks at the
    YAG crystal to determine beam position.
    """
    states = Component(PIMStates, "")

    def move_in(self):
        """
        Move the PIM to the YAG position.
        """
        self.states.value = "YAG"

    def move_out(self):
        """
        Move the PIM to the OUT position.
        """
        self.states.value = "OUT"

    def move_diode(self):
        """
        Move the PIM to the DIODE position.
        """
        self.states.value = "DIODE"

    def move(self, position, **kwargs):
        """
        Move the PIM to the inputted position.
        """
        # Adding the ability to input "IN" in addition to yag for bluesky
        if isnumber(position) and position in (1, 2, 3):
            return self.states.state.set(position)
        elif isinstance(position, str):
            if position.upper() in ("DIODE", "OUT", "IN", "YAG"): 
                if position.upper() == "IN":
                    return self.states.state.set("YAG")
                return self.states.state.set(position.upper())
        raise ValueError("Position must be a PIM valid state.")

    def mv(self, position, **kwargs):
        return self.move(position, **kwargs)

    def set(self, position, **kwargs):
        """
        Alias for move.
        """
        return self.move(position, **kwargs)
        
    @property
    @raise_if_disconnected
    def position(self):
        """
        Return the current position of the yag.
        """
        # Changing readback for "YAG" to "IN" for bluesky
        pos = self.states.state.value
        if pos == "YAG":
            return "IN"
        return pos

    @property
    @raise_if_disconnected
    def state(self):
        """
        Alias for self.position.
        """
        return self.position

    @property
    def blocking(self):
        """
        Returns if the yag is blocking the beam.
        """
        if self.states.value in ("OUT", "DIODE"):
            return False
        return True

    @property
    def inserted(self):
        """
        Alias for blocking.
        """
        return self.blocking


class PIM(PIMMotor):
    """
    PIM device that also includes a yag.
    """
    detector = FormattedComponent(PIMPulnixDetector, "{self._det_pv}",
                                  read_attrs=['stats2'])

    def __init__(self, prefix, det_pv=None, **kwargs):
        if not det_pv:
            self._section = prefix.split(":")[0]
            self._imager = prefix.split(":")[1]
            self._det_pv = "{0}:{1}:CVV:01".format(self._section, self._imager)
        else:
            self._det_pv = det_pv
        super().__init__(prefix, **kwargs)
        self.detector.check_camera = self.check_camera

    def check_camera(self):
        """
        Checks if the camera is acquiring images.
        """
        if not self.detector.acquiring:
            raise NotAcquiringError
        if not self.inserted:
            raise NotInsertedError
    
    
class PIMFee(Device):
    """
    PIM class for the PIMs in the FEE that run using Dehong's custom ioc.
    """
    # Opal
    detector = FormattedComponent(FeeOpalDetector, "{self._prefix}", 
                                name="Opal Camera")

    # Yag Motors
    zoom = FormattedComponent(ImsMotor, "{self._prefix}:CLZ:01", 
                              ioc="{self._ioc}", name="Zoom Motor")
    focus = FormattedComponent(ImsMotor, "{self._prefix}:CLF:01", 
                               ioc="{self._ioc}", name="Focus Motor")
    yag = FormattedComponent(ImsMotor, "{self._prefix}:MOTR", 
                             ioc="{self._ioc}", name="Yag Motor")
    
    # Position PV
    go = FormattedComponent(EpicsSignal, "{self._pos_pref}:YAG:GO")
    pos = FormattedComponent(EpicsSignalRO, "{self._pos_pref}:POSITION")

    def __init__(self, prefix, *, pos_pref="", ioc="", in_pos=0, out_pos=43, 
                 read_attrs=None, name=None, parent=None, 
                 configuration_attrs=None, **kwargs):        
        self._prefix = prefix
        self._pos_pref = pos_pref
        self._ioc=ioc
        self.in_pos = in_pos
        self.out_pos = out_pos

        if read_attrs is None:
            read_attrs = ['detector', 'zoom', 'focus', 'yag', 'pos']

        if configuration_attrs is None:
            configuration_attrs = ['detector', 'zoom', 'focus', 'yag', 'pos']
            
        super().__init__(prefix, read_attrs=read_attrs, name=name, parent=parent,
                         configuration_attrs=configuration_attrs, **kwargs)    

    def check_camera(self):
        """
        Checks if the camera is acquiring images and the yag is inserted.
        """
        if not self.acquiring:
            raise NotAcquiringError
        if not self.inserted:
            raise NotInsertedError

    def move_in(self):
        """
        Move the PIM to the YAG position.
        """
        return self.yag.move(self.in_pos)

    def move_out(self):
        """
        Move the PIM to the OUT position.
        """
        return self.yag.move(self.out_pos)

    def move(self, position, **kwargs):
        """
        Move the PIM to the inputted position.
        """
        if isnumber(position):
            if position == 0:
                return self.move_out()
            elif position == 1:
                return self.move_in()            
        elif isinstance(position, str):
            if position.upper() == "IN":
                return self.move_in()
            elif position.upper() == "OUT":
                return self.move_out()
        raise ValueError("Position must be a PIM valid state.")

    def mv(self, position, **kwargs):
        return self.move(position, **kwargs)
        
    @property
    @raise_if_disconnected
    def position(self):
        """
        Return the current position of the yag.
        """
        return self.states.state.value

    @property
    @raise_if_disconnected
    def state(self):
        """
        Alias for self.position.
        """
        return self.position

    @property
    @raise_if_disconnected
    def image(self):
        """
        Returns an image from the detector.
        """
        return self.detector.cam.array_data.value
                         
    @property
    @raise_if_disconnected
    def blocking(self):
        """
        Returns if the yag is blocking the beam.
        """        
        return bool(self.pos.value)

    @property
    def inserted(self):
        """
        Alias for blocking.
        """
        return not self.blocking


class PIMExceptions(Exception):
    """
    Base exception class for the PIM.
    """
    pass


class NotAcquiringError(PIMExceptions):
    """
    Error raised if an operation requiring the camera to be acquiring is
    requested while the camera is not acquiring images.
    """
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.pop("msg", "Camera currently not acquiring images.")
        super().__init__(*args, **kwargs)
    def __str__(self):
        return repr(self.msg)


class NotInsertedError(PIMExceptions):
    """
    Error raised if an operation requiring the yag be inserted is requested but
    the yag is not in the inserted position.
    """
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.pop(
            "msg", "Camera currently not in inserted position.")
        super().__init__(*args, **kwargs)
    def __str__(self):
        return repr(self.msg)
