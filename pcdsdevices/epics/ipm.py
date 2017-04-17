#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .iocdevice import IocDevice
from .states import statesrecord_class, InOutStates
from .component import Component, FormattedComponent
from .signal import EpicsSignalRO

TargetStates = statesrecord_class("TargetStates", ":OUT", ":TARGET1",
                                  ":TARGET2", ":TARGET3", ":TARGET4")


class IPM(IocDevice):
    diode = Component(InOutStates, ":DIODE")
    target = Component(TargetStates, ":TARGET")
    data = FormattedComponent(EpicsSignalRO, "{self._data}")
