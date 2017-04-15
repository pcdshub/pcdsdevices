#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define operation of the lcls attenuator IOCs
"""
from enum import Enum
from threading import Event, RLock

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
    def stuck(self):
        return self.StuckEnum(self.stuck_sig.get()).name

    def mark_stuck_in(self):
        self.stuck_sig.put(self.StuckEnum.STUCK_IN.value)

    def mark_stuck_out(self):
        self.stuck_sig.put(self.StuckEnum.STUCK_OUT.value)

    def mark_not_stuck(self):
        self.stuck_sig.put(self.StuckEnum.NOT_STUCK.value)


class AttenuatorBase(IocDevice):
    user_energy = Component(EpicsSignal, ":EDES")
    energy = Component(EpicsSignalRO, ":T_CALC.VALE")
    desired_transmission = Component(EpicsSignal, ":RDES")
    transmission = Component(EpicsSignalRO, ":R_CUR")
    transmission_ceiling = Component(EpicsSignalRO, ":R_CEIL")
    transmission_floor = Component(EpicsSignalRO, ":R_FLOOR")

    user_energy_3rd = Component(EpicsSignal, ":E3DES")
    energy_3rd = Component(EpicsSignalRO, ":T_CALC.VALH")
    desired_transmission_3rd = Component(EpicsSignal, ":R3DES")
    transmission_3rd = Component(EpicsSignalRO, ":R3_CUR")
    transmission_ceiling_3rd = Component(EpicsSignalRO, ":R3_CEIL")
    transmission_floor_3rd = Component(EpicsSignalRO, ":R3_FLOOR")

    num_att = Component(EpicsSignalRO, ":NATT")
    status = Component(EpicsSignalRO, ":STATUS")
    calcpend = Component(EpicsSignalRO, ":CALCP")

    eget_cmd = Component(EpicsSignal, ":EACT.SCAN")
    eapply_cmd = Component(EpicsSignal, ":EACT.PROC")
    mode_cmd = Component(EpicsSignal, ":MODE")
    go_cmd = Component(EpicsSignal, ":GO")

    def __init__(self, prefix, *, name=None, read_attrs=None, ioc="",
                 **kwargs):
        self._calc_event = Event()
        self._set_lock = RLock()
        if read_attrs is None:
            read_attrs = ["transmission", "transmission_3rd"]
        super().__init__(self, prefix, name=name, read_attrs=read_attrs,
                         ioc=ioc, **kwargs)

    def __call__(self, transmission=None, **kwargs):
        if transmission is None:
            return self.transmission.get()
        else:
            return self.set_transmission(transmission, **kwargs)

    def set_energy(self, energy, use3rd=False):
        if use3rd:
            self.user_energy_3rd.put(energy)
        else:
            self.user_energy.put(energy)

    def set_transmission(self, transmission, E=None, use3rd=False):
        with self._set_lock:
            if E is not None:
                self.set_energy(E, use3rd=use3rd)
            if use3rd:
                with self.calcpend.wait_for_value_context(0, old_value=1):
                    self.desired_transmission_3rd.put(transmission)
                floor = self.transmission_floor.get()
                ceiling = self.transmission_ceiling.get()
            else:
                with self.calcpend.wait_for_value_context(0, old_value=1):
                    self.desired_transmission.put(transmission)
                floor = self.transmission_floor_3rd.get()
                ceiling = self.transmission_ceiling_3rd.get()
            if abs(floor - transmission) >= abs(ceiling - transmission):
                self.go_cmd.put(3)
            else:
                self.go_cmd.put(2)
