#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define functional changes to ophyd.Device. This module really only exists
because iocadmin needs to be an LCLSDevice but we must avoid the circular
dependency that arises because iocadmin should not contain another iocadmin
record.
"""
from queue import Queue
from collections import OrderedDict
from epics.ca import CAThread as Thread
from ophyd import Device


class LCLSDeviceBase(Device):
    """
    Tweaks to Ophyd.Device
    """
    def get(self, **kwargs):
        values = OrderedDict()
        value_queue = Queue()
        threads = []
        has_ioc = False
        for attr in self.signal_names:
            values[attr] = None
            if attr == "ioc":
                has_ioc = True
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
        if has_ioc:
            values.move_to_end("ioc")
        return values

    def _get_thread(self, attr, value_queue, **kwargs):
        try:
            signal = getattr(self, attr)
            value = signal.get(**kwargs)
        except:
            value = None
        value_queue.put((attr, value))
