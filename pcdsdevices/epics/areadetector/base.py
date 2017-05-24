#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for AreaDetector Base.
"""
import logging
import ophyd
import ophyd.base
import ophyd.signal

from ..signal import EpicsSignal
from ...component import Component
from ...device import Device

logger = logging.getLogger(__name__)


class EpicsSignalWithRBV(ophyd.base.EpicsSignalWithRBV, EpicsSignal):
    pass


class ADComponent(ophyd.base.ADComponent, Component):
    pass


class ADBase(ophyd.base.ADBase, Device):
    pass
