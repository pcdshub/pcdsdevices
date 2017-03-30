#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define interface to the IOCAdmin record. This should be shared across LCLS
devices.
"""
from .lclssignal import (LCLSEpicsSignal as EpicsSignal,
                         LCLSEpicsSignalRO as EpicsSignalRO)
from .lclscomponent import LCLSComponent as Component
from .lclsdevicebase import LCLSDeviceBase as DeviceBase


class IOCAdminOld(DeviceBase):
    """
    Interface for an ioc's IOCAdmin record. This gives us information about the
    IOC's status and allows us to restart it via EPICS.

    Fully compatible IOC interface for older devices
    """
    heartbeat = Component(EpicsSignalRO, ":HEARTBEAT")
    hostname = Component(EpicsSignalRO, ":HOSTNAME")
    uptime = Component(EpicsSignalRO, ":UPTIME")
    tod = Component(EpicsSignalRO, ":TOD")
    start_tod = Component(EpicsSignalRO, ":STARTTOD")
    sysreset = Component(EpicsSignal, ":SYSRESET")


    def __init__(self, prefix, *, read_attrs=None, name=None, **kwargs):
        if read_attrs is None:
            read_attrs = ["heartbeat"]
        super().__init__(prefix, read_attrs=read_attrs, name=name, **kwargs)

    def soft_reboot(self):
        """
        Stop the IOC process in the procServ, letting the procServ restart the
        IOC process.
        """
        self.sysreset.put(1)

class IOCAdmin(IOCAdminOld):
    """
    Interface for an ioc's IOCAdmin record. This gives us information about the
    IOC's status and allows us to restart it via EPICS.

    Includes the latest additions to the record
    """
    port = Component(EpicsSignalRO, ":CA_SRVR_PORT")
    # I think there's a way to implement hard_reboot with this PV
