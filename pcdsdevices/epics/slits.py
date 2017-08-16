#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ophyd.pv_positioner import PVPositioner

from .signal import EpicsSignal, EpicsSignalRO
from .component import Component, FormattedComponent
from .device import Device
from .iocdevice import IocDevice


class SlitPositioner(PVPositioner, Device):
    """
    PVPositioner subclass for the slit center and width pseudomotors.
    """
    setpoint = FormattedComponent(EpicsSignal,
                                  "{self.prefix}:{self._dirshort}_REQ")
    readback = FormattedComponent(EpicsSignalRO,
                                  "{self.prefix}:ACTUAL_{self._dirlong}")
    done = Component(EpicsSignalRO, ":DMOV")

    def __init__(self, prefix="", *, slit_type="", limits=None, name=None,
                 read_attrs=None, parent=None, egu="", **kwargs):
        if parent is not None:
            prefix = parent.prefix + prefix
        self._dirlong = slit_type
        self._dirshort = slit_type[:4]
        if read_attrs is None:
            read_attrs = ["readback"]
        super().__init__(prefix, limits=limits, name=name,
                         read_attrs=read_attrs, parent=parent, egu=egu,
                         **kwargs)


class Slits(IocDevice):
    """
    Beam slits with combined motion for center and width.
    """
    xcenter = Component(SlitPositioner, slit_type="XCENTER", egu="mm")
    xwidth = Component(SlitPositioner, slit_type="XWIDTH", egu="mm")
    ycenter = Component(SlitPositioner, slit_type="YCENTER", egu="mm")
    ywidth = Component(SlitPositioner, slit_type="YWIDTH", egu="mm")
    blocked = Component(EpicsSignalRO, ":BLOCKED")
    open_cmd = Component(EpicsSignal, ":OPEN")
    close_cmd = Component(EpicsSignal, ":CLOSE")
    block_cmd = Component(EpicsSignal, ":BLOCK")

    def __init__(self, prefix, *, ioc="", read_attrs=None, name=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = ['xcenter', 'xwidth', 'ycenter', 'ywidth', 'blocked']
        super().__init__(prefix, ioc=ioc, read_attrs=read_attrs, name=name,
                         **kwargs)

    def move(self,width,wait=True,**kwargs):
        """
        Set the dimensions of the width/height of the gap to width paramater.
        It's OK to only return one of the statuses because they share the same
        completion flag (I think).

        Paramters
        ---------
        width : float
            target width for slits in both x and y axis. EGU: mm

        wait : bool
            If true, block until move is completed

        Returns
        -------
        status : MoveStauts
            status object of the move

        """
        self.xwidth.move(width,wait=False,**kwargs)
        return self.ywidth.move(width,wait=wait,**kwargs)



    def set(self,width,wait=True,**kwargs):
        """
        alias for move method 
        """
        return self.move(width,wait,**kwargs)

    def stage(self):
        """
        Record starting position of slits. This allows @stage_wrapper to make
        plans involving the slits to return to their starting positions.
        """
        self.stage_cache_xwidth = self.xwidth.position
        self.stage_cache_ywidth = self.ywidth.position
        self.stage_cache_xcenter = self.xcenter.position
        self.stage_cache_ycenter = self.ycenter.position
        return super().stage()

    def unstage(self):
        """
        Place slits back in their starting positions. This allows 
        @stage_wrapper to make plans involving the slits to return to their
        starting positions.
        """
        self.xwidth.move(self.stage_cache_xwidth,wait=False)
        self.ywidth.move(self.stage_cache_ywidth,wait=False)
        self.xcenter.move(self.stage_cache_xcenter,wait=False)
        self.ycenter.move(self.stage_cache_ycenter,wait=True)
        return super().unstage()

    def open(self):
        self.open_cmd.put(1)

    def close(self):
        self.close_cmd.put(1)

    def block(self):
        self.block_cmd.put(1)
