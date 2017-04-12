#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for Epics Signals
"""

from ophyd.signal import EpicsSignalBase, EpicsSignal, EpicsSignalRO


class PcdsEpicsSignalBase(EpicsSignalBase):
    pass


class PcdsEpicsSignal(EpicsSignal, PcdsEpicsSignalBase):
    pass


class PcdsEpicsSignalRO(EpicsSignalRO, PcdsEpicsSignalBase):
    pass
