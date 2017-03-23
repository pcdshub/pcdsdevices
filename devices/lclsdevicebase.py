#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define functional changes to ophyd.Device. This module really only exists
because iocadmin needs to be an LCLSDevice but we must avoid the circular
dependency that arises because iocadmin should not contain another iocadmin
record.
"""
from queue import Queue
from epics.ca import CAThread as Thread
from ophyd import Device


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
        try:
            signal = getattr(self, attr)
            value = signal.get(**kwargs)
        except:
            value = None
        value_queue.put((attr, value))
