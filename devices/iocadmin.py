#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interface for LCLS's iocAdmin record. This is an EPICS module that provides
basic IOC information over channel access.
"""
from ophyd import Device, Component, EpicsSignal, EpicsSignalRO

class IOCAdmin(Device):
    heartbeat = Component(EpicsSignalRO, ":HEARTBEAT")
    hostname = Component(EpicsSignalRO, ":HOSTNAME")
    uptime = Component(EpicsSignalRO, ":UPTIME")
    tod = Component(EpicsSignalRO, ":TOD")
    start_tod = Component(EpicsSignalRO, ":STARTTOD")
    sysreset = Component(EpicsSignal, ":SYSRESET")

    def soft_reboot(self):
        self.sysreset.put(1)
