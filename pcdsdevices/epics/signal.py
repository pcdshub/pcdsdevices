#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for Epics Signals
"""
import logging
import ophyd.signal
import ophyd.base
from ..signal import Signal

logger = logging.getLogger(__name__)


class EpicsSignalBase(Signal, ophyd.signal.EpicsSignalBase):
    pass


class EpicsSignal(EpicsSignalBase, ophyd.signal.EpicsSignal):
    def put(self, value, force=False, connection_timeout=1.0,
            use_complete=None, **kwargs):
        logger.debug("Putting PV value of %s from %s to %s",
                     self.name or self, self.get(), value)
        super().put(value, force=force, connection_timeout=connection_timeout,
                    use_complete=use_complete, **kwargs)

class EpicsSignalRO(EpicsSignalBase, ophyd.signal.EpicsSignalRO):
    pass
