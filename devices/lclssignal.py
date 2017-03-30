#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for Epics Signals
"""

from ophyd.signal import EpicsSignalBase, EpicsSignal, EpicsSignalRO


class LCLSEpicsSignalBase(EpicsSignalBase):
    pass


class LCLSEpicsSignal(EpicsSignal, LCLSEpicsSignalBase):
    pass


class LCLSEpicsSignalRO(EpicsSignalRO, LCLSEpicsSignalBase):
    pass
