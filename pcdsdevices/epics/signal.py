#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for Epics Signals
"""
import logging
import math

import ophyd.signal
from ..signal import Signal

logger = logging.getLogger(__name__)


class EpicsSignalBase(ophyd.signal.EpicsSignalBase, Signal):
    pass


class EpicsSignal(ophyd.signal.EpicsSignal, EpicsSignalBase):
    def put(self, value, force=False, connection_timeout=1.0,
            use_complete=None, **kwargs):
        logger.debug("Putting PV value of %s from %s to %s",
                     self.name or self, self.get(), value)

        if not isinstance(value, str) and math.isnan(value):
            raise RuntimeError("Recieved a NaN value in EPICS put")
        else:
            super().put(value, force=force,
                        connection_timeout=connection_timeout,
                        use_complete=use_complete, **kwargs)


class EpicsSignalRO(ophyd.signal.EpicsSignalRO, EpicsSignalBase):
    pass


class FakeSignal(Signal):
    """
    Fake signal to appease ophyd.
    """
    def __init__(self, *args, **kwargs):
        self.stored_val = 0
        super().__init__(*args, **kwargs)

    def get(self):
        return self.stored_val
