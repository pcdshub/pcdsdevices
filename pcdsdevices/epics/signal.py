#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for Epics Signals
"""
import ophyd.signal
from ..signal import Signal


class EpicsSignalBase(ophyd.signal.EpicsSignalBase, Signal):
    pass


class EpicsSignal(ophyd.signal.EpicsSignal, EpicsSignalBase):
    pass


class EpicsSignalRO(ophyd.signal.EpicsSignalRO, EpicsSignalBase):
    pass
