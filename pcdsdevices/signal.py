#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for ophyd.signal
"""
from threading import Event, RLock
from contextlib import contextmanager
import ophyd.signal


class Signal(ophyd.signal.Signal):
    def __init__(self, *, value=None, timestamp=None, name=None, parent=None,
                 tolerance=None, rtolerance=None):
        self._wfv_event = Event()
        self._wfv_lock = RLock()
        super().__init__(self, value=value, timestamp=timestamp, name=name,
                         parent=parent, tolerance=tolerance,
                         rtolerance=rtolerance)

    def wait_for_value(self, value, old_value=None, timeout=None, prep=True):
        with self._wfv_lock:
            if prep:
                self._wait_for_value_prep(value, old_value)
            if timeout is not None:
                timeout = float(timeout)
            ok = self._wfv_event.wait(timeout)
            self.clear_sub(self._wfv_cb)
        return ok

    def _wait_for_value_prep(self, value, old_value):
        with self._wfv_lock:
            self._wfv_event.clear()
            self.subscribe(self._wait_for_value_cb(value, old_value),
                           event_type=self.SUB_VALUE)

    def _wait_for_value_cb(self, value, old_value):
        def cb(self, *args, obj, sub_type, **kwargs):
            ok = True
            if old_value is not None:
                old = kwargs["old_value"]
                ok = ok and (old == old_value)
            new = kwargs["value"]
            ok = ok and (new == value)
            if ok:
                self._wfv_event.set()
        self._wfv_cb = cb
        return cb

    @contextmanager
    def wait_for_value_context(self, value, old_value=None, timeout=None):
        with self._wfv_lock:
            self._wait_for_value_prep(value, old_value)
            try:
                yield
            finally:
                self.wait_for_value(value, old_value=old_value,
                                    timeout=timeout, prep=False)
