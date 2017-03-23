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
    heartbeat = Component(EpicsSignalRO, ":HEARTBEAT", lazy=True)
    hostname = Component(EpicsSignalRO, ":HOSTNAME", lazy=True)
    # Pulsepicker ioc doesn't have this one...
    # port = Component(EpicsSignalRO, ":CA_SRVR_PORT", lazy=True)
    uptime = Component(EpicsSignalRO, ":UPTIME", lazy=True)
    tod = Component(EpicsSignalRO, ":TOD", lazy=True)
    start_tod = Component(EpicsSignalRO, ":STARTTOD", lazy=True)
    sysreset = Component(EpicsSignal, ":SYSRESET", lazy=True)

    def soft_reboot(self):
        """
        Stop the IOC process in the procServ, letting the procServ restart the
        IOC process.
        """
        self.sysreset.put(1)
