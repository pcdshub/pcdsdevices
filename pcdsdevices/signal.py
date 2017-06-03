#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from threading import Event, RLock
from contextlib import contextmanager

import ophyd.signal
# from ophyd.utils import doc_annotation_forwarder

logger = logging.getLogger(__name__)


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

    # @doc_annotation_forwarder(ophyd.signal.Signal)
    def put(self, value, *, timestamp=None, force=False, **kwargs):
        #logger.debug("Changing stored value of %s from %s to %s at time=%s",
        #             self.name or self, self.get(), value, timestamp)
        super().put(value, timestamp=timestamp, force=force, **kwargs)

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
        logger.debug("Attempting to acquire wait for value rlock in %s",
                     self.name or self)
        with self._wfv_lock:
            logger.debug("Acquired wait for value rlock in %s",
                         self.name or self)
            if prep:
                self._wait_for_value_prep(value, old_value)
            if timeout is not None:
                timeout = float(timeout)
            logger.debug("Waiting for value callback in %s for value=%s, " +
                         "old_value=%s, timeout=%s",
                         self.name or self, value, old_value, timeout)
            ok = self._wfv_event.wait(timeout)
            logger.debug("Done waiting in %s, timedout=%s",
                         self.name or self, not ok)
            self.clear_sub(self._wfv_cb)
        logger.debug("Released wait for value rlock in %s", self.name or self)
        return ok

    def _wait_for_value_prep(self, value, old_value=None):
        """
        Clear the event flags and set the subscription.
        """
        logger.debug("Attempting to acquire prep rlock in %s",
                     self.name or self)
        with self._wfv_lock:
            logger.debug("Acquired prep rlock in %s", self.name or self)
            self._wfv_event.clear()
            self.subscribe(self._wait_for_value_cb(value, old_value))
        logger.debug("Released prep rlock in %s", self.name or self)

    def _wait_for_value_cb(self, value, old_value=None):
        """
        Create a callback function that sets the internal flag when we see the
        desired transition.

        Returns
        -------
        cb: function
        """
        def cb(*args, obj, sub_type, **kwargs):
            logger.debug("Calling wfv callback in %s", self.name or self)
            ok = True
            if old_value is not None:
                old = kwargs["old_value"]
                ok = ok and (old == old_value)
                logger.debug("wfv callback in %s got old_value=%s",
                             self.name or self, old_value)
            new = kwargs["value"]
            ok = ok and (new == value)
            logger.debug("wfv callback in %s got value=%s",
                         self.name or self, value)
            if ok:
                logger.debug("Wait finished in %s", self.name or self)
                self._wfv_event.set()
            else:
                logger.debug("Wait not done in %s", self.name or self)
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
        logger.debug("Attempting to acquire context rlock in %s",
                     self.name or self)
        with self._wfv_lock:
            logger.debug("Acquired context rlock in %s", self.name or self)
            self._wait_for_value_prep(value, old_value)
            try:
                yield
            finally:
                self.wait_for_value(value, old_value=old_value,
                                    timeout=timeout, prep=False)
        logger.debug("Released context rlock in %s", self.name or self)
