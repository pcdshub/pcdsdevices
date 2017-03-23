#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define common features among LCLS devices. This includes things like the
iocAdmin module that all LCLS devices share but are not guaranteed outside of
LCLS.
"""
from queue import Queue
from epics.ca import CAThread as Thread
from ophyd import Device, FormattedComponent
from .iocadmin import IOCAdmin


class LCLSDeviceBase(Device):
    """
    Tweaks to Ophyd.Device
    """
    def get(self, **kwargs):
        values = {}
        value_queue = Queue()
        threads = []
        for attr in self.signal_names:
            get_thread = Thread(target=self._get_thread,
                                args=(attr, value_queue),
                                kwargs=kwargs)
            threads.append(get_thread)
            get_thread.start()
        for t in threads:
            t.join()
        while not value_queue.empty():
            attr, value = value_queue.get()
            values[attr] = value
        return values

    def _get_thread(self, attr, value_queue, **kwargs):
        signal = getattr(self, attr)
        try:
            value = signal.get(**kwargs)
        except:
            value = None
        value_queue.put((attr, value))


class LCLSDevice(LCLSDeviceBase):
    """
    Ophyd subclass for devices that represent LCLS-specific IOCs.
    """
    ioc = FormattedComponent(IOCAdmin, "{self._iocadmin}")

    def __init__(self, prefix, *, ioc="", read_attrs=None, name=None,
                 **kwargs):
        self._iocadmin = ioc
        super().__init__(prefix, read_attrs=read_attrs, name=name, **kwargs)
