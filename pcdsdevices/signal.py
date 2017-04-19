#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for ophyd.signal
"""
from threading import Event, RLock
from contextlib import contextmanager
import ophyd.signal


class Signal(ophyd.signal.Signal):
    """
    Signal subclass with pcds overrides. This currently defines some methods
    for waiting for signals to change to specific values on their default
    callbacks.
    """
    def __init__(self, *, value=None, timestamp=None, name=None, parent=None,
                 tolerance=None, rtolerance=None):
        self._wfv_event = Event()
        self._wfv_lock = RLock()
        super().__init__(value=value, timestamp=timestamp, name=name,
                         parent=parent, tolerance=tolerance,
                         rtolerance=rtolerance)

    def wait_for_value(self, value, old_value=None, timeout=None, prep=True):
        """
        Pause the thread until the signal's value changes to value after the
        default sub callback.

        Parameters
        ----------
        value: object
            The desired signal value. There is no type restriction.
        old_value: object, optional
            If provided, we'll wait to change from old_value to value instead
            of just waiting on value. This may be useful to wait for specific
            transitions.
        timeout: number, optional
            Stop waiting after this many seconds. This can be any object that
            will accept being cast to float with a float(timeout) call.
        prep: bool, optional
            If False, skip the step where we prepare the event flag. True by
            default. Do not set this parameter if you don't know what you're
            doing.
        """
        with self._wfv_lock:
            if prep:
                self._wait_for_value_prep(value, old_value)
            if timeout is not None:
                timeout = float(timeout)
            ok = self._wfv_event.wait(timeout)
            self.clear_sub(self._wfv_cb)
        return ok

    def _wait_for_value_prep(self, value, old_value=None):
        """
        Clear the event flags and set the subscription.
        """
        with self._wfv_lock:
            self._wfv_event.clear()
            self.subscribe(self._wait_for_value_cb(value, old_value))

    def _wait_for_value_cb(self, value, old_value=None):
        """
        Create a callback function that sets the internal flag when we see the
        desired transition.

        Returns
        -------
        cb: function
        """
        def cb(*args, obj, sub_type, **kwargs):
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
        """
        Context manager for waiting for value. Clears the flag, sets up
        subscription callback, calls user code, and then waits until the flag
        has been set.

        Use this when you need to watch for a transition that can occur while
        your main thread needs to be doing something else.
        """
        with self._wfv_lock:
            self._wait_for_value_prep(value, old_value)
            try:
                yield
            finally:
                self.wait_for_value(value, old_value=old_value,
                                    timeout=timeout, prep=False)
