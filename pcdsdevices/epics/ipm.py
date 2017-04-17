#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .iocdevice import IocDevice
from .state import statesrecord_class, InOutStates
from .component import Component, FormattedComponent
from .signal import EpicsSignalRO

TargetStates = statesrecord_class("TargetStates", ":OUT", ":TARGET1",
                                  ":TARGET2", ":TARGET3", ":TARGET4")


class IPM(IocDevice):
    """
    Standard intensity position monitor. Consists of two stages, one for the
    diode and one for the target. This creates a scalar readback that is also
    available over EPICS.
    """
    diode = Component(InOutStates, ":DIODE")
    target = Component(TargetStates, ":TARGET")
    data = FormattedComponent(EpicsSignalRO, "{self._data}")

    def __init__(self, prefix, *, data="", ioc="", name=None, parent=None,
                 read_attrs=None, **kwargs):
        self._data = data
        if read_attrs is None:
            read_attrs = ["data"]
        super().__init__(self, prefix, ioc=ioc, name=name, parent=parent,
                         read_attrs=read_attrs, **kwargs)

    def target_out(self):
        """
        Move the target to the OUT position.
        """
        self.target.value = "OUT"

    def target_in(self, target):
        """
        Move the target to one of the target positions

        Parameters
        ----------
        target, int
            Number of which target to move in. Must be one of 1, 2, 3, 4.
        """
        target = int(target)
        if 1 <= target <= 4:
            self.target.value = "TARGET{}".format(target)

    def diode_in(self):
        """
        Move the diode to the in position.
        """
        self.diode.value = "IN"

    def diode_out(self):
        """
        Move the diode to the out position.
        """
        self.diode.value = "OUT"
