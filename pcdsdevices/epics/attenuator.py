#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define operation of the lcls attenuator IOCs
"""
from enum import Enum

from .device import Device, IocDevice
from .component import Component
from .signal import EpicsSignal, EpicsSignalRO


class Filter(Device):
    state_sig = Component(EpicsSignal, ":STATE", write_pv=":GO")
    thickness_sig = Component(EpicsSignal, ":THICK")
    material_sig = Component(EpicsSignal, ":MATERIAL")
    stuck_sig = Component(EpicsSignal, ":IS_STUCK")

    FilterStates = Enum("FilterStates", "UNKNOWN IN OUT")
    StuckEnum = Enum("StuckEnum", "NOT_STUCK STUCK_IN STUCK_OUT")

    def __init__(self, prefix, *, name=None, read_attrs=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['state_sig']
        super().__init__(self, prefix, name=name, read_attrs=read_attrs,
                         **kwargs)

    @property
    def value(self):
        return self.FilterStates(self.state_sig.get()).name

    def move_in(self):
        self.state_sig.put(self.FilterStates.IN.value)

    def move_out(self):
        self.state_sig.put(self.FilterStates.OUT.value)

    @property
    def stuck(self)
        return self.StuckEnum(self.stuck_sig.get()).name

    def mark_stuck_in(self):
        self.stuck_sig.put(self.StuckEnum.STUCK_IN.value)

    def mark_stuck_out(self):
        self.stuck_sig.put(self.StuckEnum.STUCK_OUT.value)

    def mark_not_stuck(self):
        self.stuck_sig.put(self.StuckEnum.NOT_STUCK.value)


class Attenuator(IocDevice):
    def __init__(self, prefix, *, name=None, read_attrs=None, ioc="",
                 **kwargs):
        if read_attrs is None:
            read_attrs = []
        super().__init__(self, prefix, name=name, read_attrs=read_attrs,
                         ioc=ioc, **kwargs)
