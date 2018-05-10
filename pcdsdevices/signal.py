"""
Module to define ophyd Signal subclass utilities.
"""
import logging
from threading import RLock, Thread

import numpy as np
from ophyd.signal import Signal

logger = logging.getLogger(__name__)


class AggregateSignal(Signal):
    """
    Signal that is composed of a number of other signals.

    This class exists to handle the group subscriptions without repeatedly
    getting the values of all the subsignals at all times.

    Attributes
    ----------
    _cache: dict
        Mapping from signal to last known value

    _sub_signals: list
        Signals that contribute to this signal.
    """
    _update_only_on_change = True

    def __init__(self, *, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self._cache = {}
        self._has_subscribed = False
        self._lock = RLock()
        self._sub_signals = []

    def _calc_readback(self):
        """
        Override this with a calculation to find the current state given the
        cached values.

        Returns
        -------
        readback:
            The result of the calculation.
        """
        raise NotImplementedError('Subclasses must implement _calc_readback')

    def _insert_value(self, signal, value):
        """
        Update the cache with one value and recalculate
        """
        with self._lock:
            self._cache[signal] = value
            self._update_state()
            return self._readback

    def _update_state(self):
        """
        Recalculate the state.
        """
        with self._lock:
            self._readback = self._calc_readback()

    def get(self, **kwargs):
        """
        Update all values and recalculate
        """
        with self._lock:
            for signal in self._sub_signals:
                self._cache[signal] = signal.get(**kwargs)
            self._update_state()
            return self._readback

    def put(self, value, **kwargs):
        raise NotImplementedError('put should be overriden in the subclass')

    def subscribe(self, cb, event_type=None, run=True):
        """
        Set up a callback function to run at specific times.

        See the ``ophyd`` documentation for details.
        """
        cid = super().subscribe(cb, event_type=event_type, run=run)
        if event_type in (None, self.SUB_VALUE) and not self._has_subscribed:
            # We need to subscribe to ALL relevant signals!
            for signal in self._sub_signals:
                signal.subscribe(self._run_sub_value, run=False)
            self.get()  # Ensure we have a full cache
        return cid

    def _run_sub_value(self, *args, **kwargs):
        kwargs.pop('sub_type')
        sig = kwargs.pop('obj')
        kwargs.pop('old_value')
        value = kwargs['value']
        with self._lock:
            old_value = self._readback
            # Update just one value and assume the rest are cached
            # This allows us to run subs without EPICS gets
            value = self._insert_value(sig, value)
            if value != old_value or not self._update_only_on_change:
                self._run_subs(sub_type=self.SUB_VALUE, obj=self, value=value,
                               old_value=old_value)


class AvgSignal(Signal):
    """
    Signal that acts as a rolling average of another signal
    """
    def __init__(self, signal, averages, *, name, parent=None, **kwargs):
        super().__init__(name=name, parent=parent, **kwargs)
        if isinstance(signal, str):
            signal = getattr(parent, signal)
        self.sig = signal
        self.lock = RLock()
        self.averages = averages
        self._con = False
        t = Thread(target=self._init_subs, args=())
        t.start()

    def _init_subs(self):
        self.sig.wait_for_connection()
        self.sig.subscribe(self._update_avg)
        self._con = True

    @property
    def connected(self):
        return self._con

    @property
    def averages(self):
        return self._avg

    @averages.setter
    def averages(self, avg):
        with self.lock:
            self._avg = avg
            self.index = 0
            self.values = np.empty(avg)
            self.values.fill(np.nan)

    def _update_avg(self, *args, value, **kwargs):
        with self.lock:
            self.values[self.index] = value
            self.index += 1
            if self.index == len(self.values):
                self.index = 0
            self.put(np.nanmean(self.values))
