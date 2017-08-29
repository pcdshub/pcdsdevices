#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import copy
import random
import logging
import threading
from functools import wraps
import inspect

import epics
import numpy as np


class FakeEpicsPV(object):
    """
    Fake EpicsPV that mocks the API `epics.PV`

    Keep in mind this is an incredibly simple implementation, after being
    intialized as `None` the PV will hold whatever value you `put` to it. This
    triggers all subscribed callbacks.

    Notes
    -----
    A few gotchas to keep in mind when writing tests
        - Using `@using_fake_epics_pv` is slightly complex when using fixtures.
          Because some of `ophyd` instantiates Epics PVs lazily it is best
          practice to have a wrapper around both the fixture and test
        - A signal that has separate a `_read_pv` and `_write_pv` will only put
          to the write side, this will not change the readback at all
        - Calling `set` on a signal launches another thread to actually change
          the value. This means if you are planning on checking the result of a
          method that calls `set` underneath, you should put a small `sleep`
          afterwards to let the thread create itself and get to the point of
          actually changing the value. The other way around this is to use a
          `wait` in your method. This will block the main thread until the
          set_thread catches up. For this to work you need to make sure that
          `put_complete` is set to `True` on the EpicsSignal you are calling
          `set` on
    """
    _connect_delay = (0.05, 0.1)
    _update_rate = 0.1
    _pv_idx = 0
    auto_monitor = True

    def __init__(self, pvname, form=None,
                 callback=None, connection_callback=None,
                 auto_monitor=True, enum_strs=None,
                 **kwargs):

        self._pvname = pvname
        self._connection_callback = connection_callback
        self._form = form
        self._auto_monitor = auto_monitor
        self._value = 0
        self._connected = True
        self._running = True
        self.enum_strs = enum_strs
        FakeEpicsPV._pv_idx += 1
        self._idx = FakeEpicsPV._pv_idx

        self._update = True
        self._thread = threading.Thread(target=self._update_loop)
        self._thread.daemon = True
        self._thread.start()

        self.callbacks = dict()
        if callback:
            self.add_callback(callback)

    def __del__(self):
        self.clear_callbacks()
        self._running = False

    def get_timevars(self):
        pass

    def get_ctrlvars(self):
        pass

    @property
    def connected(self):
        """
        PV is connected
        """
        return self._connected


    def _update_loop(self):
        """
        Connect PV and run connection callback
        """
        if self._connection_callback is not None:
            self._connection_callback(pvname=self._pvname, conn=True, pv=self)

        if self._pvname in ('does_not_connect', ):
            return

        self._connected = True


    def wait_for_connection(self, timeout=None):
        """
        Wait for PV connection
        """
        if self._pvname in ('does_not_connect', ):
            return False

        while not self._connected:
            time.sleep(0.05)

        return True


    @property
    def lower_ctrl_limit(self):
        return 0.


    @property
    def upper_ctrl_limit(self):
        return 1.


    def run_callbacks(self):
        """
        Run all stored callbacks
        """
        for index in sorted(list(self.callbacks.keys())):
            if not self._running:
                break
            self.run_callback(index)


    def run_callback(self, index):
        """
        Run an individual callback
        """
        fcn = self.callbacks[index]
        kwd = dict(pvname=self._pvname,
                   count=1,
                   nelm=1,
                   type=None,
                   typefull=None,
                   ftype=None,
                   access='rw',
                   chid=self._idx,
                   read_access=True,
                   write_access=True,
                   value=self.value,
                   )
        kwd['cb_info'] = (index, self)
        if hasattr(fcn, '__call__'):
            fcn(**kwd)


    def add_callback(self, callback=None, index=None, run_now=False,
                     with_ctrlvars=True):
        """
        Add a callback to the PV
        """
        if hasattr(callback, '__call__'):
            if index is None:
                index = 1
                if len(self.callbacks) > 0:
                    index = 1 + max(self.callbacks.keys())
            self.callbacks[index] = callback
        if run_now:
            if self.connected:
                self.run_callback(index)
        return index

    def remove_callback(self, index=None):
        if index in self.callbacks:
            self.callbacks.pop(index)

    def clear_callbacks(self):
        self.callbacks.clear()

    @property
    def precision(self):
        return 0

    @property
    def units(self):
        return str(None)

    @property
    def timestamp(self):
        """
        Simulated timestamp
        """
        return time.time()

    @property
    def pvname(self):
        """
        Name of PV
        """
        return self._pvname

    @property
    def value(self):
        """
        Last set value
        """
        return self._value

    def __repr__(self):
        return '<FakePV %s value=%s>' % (self._pvname, self.value)

    def get(self, as_string=False, use_numpy=False,
            use_monitor=False):
        """
        Simulate and EPICS caget
        """
        if as_string:
            #Return list of enums
            if isinstance(self.value, list):
                if self.enum_strs:
                    return [self.enum_strs[_] for _ in self.value]
                return list(self.value)
            #Return single string
            if isinstance(self.value, str):
                return self.value
            #Return single enum
            else:
                if self.enum_strs:
                    return self.enum_strs[self.value]
                return str(self.value)
        #Return numpy array
        elif use_numpy:
            return np.array(self.value)
        #Otherwise return the value as is
        else:
            return self.value


    def put(self, value, wait=False, timeout=30.0,
            use_complete=False, callback=None, callback_data=None):
        """
        Simulate a EPICS caput
        """
        #Update stored value
        self._update = False
        self._value = value
        #Run callbacks
        self.run_callbacks()
        #Acknowledge put completion
        if use_complete and callback:
            callback()

def using_fake_epics_pv(fcn):
    @wraps(fcn)
    def wrapped(*args, **kwargs):
        pv_backup = epics.PV
        epics.PV = FakeEpicsPV
        try:
            return fcn(*args, **kwargs)
        finally:
            epics.PV = pv_backup

    return wrapped

def get_classes_in_module(module, subcls=None):
    classes = []
    all_classes = inspect.getmembers(module)
    for _, cls in all_classes:
        try:
            if cls.__module__ == module.__name__:
                if subcls is not None:
                    try:
                        if not issubclass(cls, subcls):
                            continue
                    except TypeError:
                        continue
                classes.append(cls)
        except AttributeError:
            pass    
    return classes
