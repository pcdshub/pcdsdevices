#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for AreaDetector Base.
"""
import logging
import ophyd
import signal
from ophyd import base

from ..signal import EpicsSignal
from ...component import Component
from ...device import Device

logger = logging.getLogger(__name__)


class EpicsSignalWithRBV(base.EpicsSignalWithRBV, EpicsSignal):
    pass


class ADComponent(base.ADComponent, Component):
    pass


class ADBase(base.ADBase, Device):
    pass
