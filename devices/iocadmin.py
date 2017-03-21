#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define interface to the IOCAdmin record. This should be shared across LCLS
devices.
"""
from ophyd import Device, Component, EpicsSignal, EpicsSignalRO


class IOCAdmin(Device):
    """
    Interface for an ioc's IOCAdmin record. This gives us information about the
    IOC's status and allows us to restart it via EPICS.
    """
    heartbeat = Component(EpicsSignalRO, ":HEARTBEAT")
    hostname = Component(EpicsSignalRO, ":HOSTNAME")
    port = Component(EpicsSignalRO, ":CA_SRVR_PORT")
    uptime = Component(EpicsSignalRO, ":UPTIME")
    tod = Component(EpicsSignalRO, ":TOD")
    start_tod = Component(EpicsSignalRO, ":STARTTOD")
    sysreset = Component(EpicsSignal, ":SYSRESET")

    def soft_reboot(self):
        """
        Stop the IOC process in the procServ, letting the procServ restart the
        IOC process.
        """
        self.sysreset.put(1)
