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

    def __init__(self, prefix=None, **kwargs):
        self._prefix = prefix
        super().__init__(prefix, **kwargs)
        if self.prefix is None and self.parent is None:
            raise ValueError("No prefix or parent provided to IOCAdmin Device")

    def soft_reboot(self):
        """
        Stop the IOC process in the procServ, letting the procServ restart the
        IOC process.
        """
        self.sysreset.put(1)

    @property
    def prefix(self):
        """
        Delegate finding information about the iocAdmin prefix to the parent,
        if one is available and we have not explicitly provided a prefix.
        """
        # If a prefix was provided, use it.
        if self._prefix is not None:
            return self._prefix
        # Go through parents in succession until we find an _iocadmin
        # attribute that isn't empty.
        next_parent = self.parent
        while next_parent is not None:
            try:
                prefix = next_parent._iocadmin
                if prefix:
                    return prefix
            except AttributeError:
                pass
            finally:
                next_parent = next_parent.parent
        # We didn't find any valid prefixes, so make this object do nothing.
        return ""
