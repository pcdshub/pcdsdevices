#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from ophyd.utils.epics_pvs import (raise_if_disconnected, AlarmSeverity)

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
    image2 = Component(ImagePlugin, ":IMAGE2:", read_attrs=['array_data'])
    stats1 = Component(StatsPlugin, ":Stats1:", read_attrs=['centroid'])
    stats2 = Component(StatsPlugin, ":Stats2:", read_attrs=['centroid'])
    proc1 = Component(ProcessPlugin, ":Proc1:", read_attrs=['num_filter'])
        

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
        if isnumber(position) and position in (1, 2, 3):
            return self.states.state.set(position)
        elif isinstance(position, str):
            if position.upper() in ("DIODE", "YAG", "OUT"): 
                return self.states.state.set(position.upper())
        raise ValueError("Position must be a PIM valid state.")

    def set(self, position, **kwargs):
        """
        Alias for move.
        """
        self.move(position, **kwargs)
        
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
    def blocking(self):
        if self.states.value in ("OUT", "DIODE"):
            return False
        return True

    @property
    def inserted(self):
        return not self.blocking


class PIM(PIMMotor):
    """
    PIM device that also includes a yag.
    """
    detector = FormattedComponent(PIMPulnixDetector, 
                                  "{self._section}:{self._imager}:CVV:01")
    # motor = Component(PIMMotor, "")

    def __init__(self, prefix, **kwargs):
        self._section = prefix.split(":")[0]
        self._imager = prefix.split(":")[1]
        super().__init__(prefix, **kwargs)
        

    def check_camera(self):
        if not self.acquiring:
            raise NotAcquiringError
        if not self.inserted:
            raise NotInsertedError

    @property
    @raise_if_disconnected
    def image(self):
        """Returns an image from the detector."""
        return self.detector.image2.array_data.value

    @property
    @raise_if_disconnected
    def acquiring(self):
        """Checks to see if the camera is currently acquiring iamges."""
        return bool(self.detector.cam.acquire.value)

    @acquiring.setter
    def acquiring(self, val):
        """Setter for acquiring."""
        self.detector.cam.acquire.put(bool(val))

    @property
    @raise_if_disconnected
    def centroid_x(self):
        """Returns the beam centroid in x."""
        self.check_camera()
        return self.detector.stats2.centroid.x.value

    @property
    @raise_if_disconnected
    def centroid_y(self):
        """Returns the beam centroid in y."""
        self.check_camera()
        return self.detector.stats2.centroid.x.value

    @property
    def centroid(self):
        """Returns the beam centroid in y."""
        return (self.centroid_x, self.centroid_y)
    
    
class PIMFee(Device):
    """
    YAG detector using Dehongs IOC.
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
        """Returns an image from the detector."""
        return self.detector.cam.array_data.value
                         
    @property
    @raise_if_disconnected
    def blocking(self):
        return bool(self.pos.value)

    @property
    def inserted(self):
        return not self.blocking

    @property
    @raise_if_disconnected
    def acquiring(self):
        """Checks to see if the camera is currently acquiring iamges."""
        return bool(self.detector.cam.acquire.value)

    @acquiring.setter
    def acquiring(self, val):
        """Setter for acquiring."""
        self.detector.cam.acquire.put(bool(val))

    @property
    @raise_if_disconnected
    def centroid_x(self):
        """Returns the beam centroid in x."""
        self.check_camera()
        raise NotImplementedError

    @property
    @raise_if_disconnected
    def centroid_y(self):
        """Returns the beam centroid in y."""
        self.check_camera()
        raise NotImplementedError

    @property
    def centroid(self):
        """Returns the beam centroid in y."""
        raise NotImplementedError


class PIMExceptions(Exception):
    pass


class NotAcquiringError(PIMExceptions):
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.pop("msg", "Camera currently not acquiring images.")
        super().__init__(*args, **kwargs)
    def __str__(self):
        return repr(self.msg)


class NotInsertedError(PIMExceptions):
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.pop("msg", "Camera currently not in inserted position.")
        super().__init__(*args, **kwargs)
    def __str__(self):
        return repr(self.msg)
