#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for AreaDetector Base. These are here in anticipation of any changes
that will be necessary down the line, so higher level classes do not need to be
rewritten.
"""
import logging

import ophyd
import signal
from ophyd import base

from ...device import Device
from ..signal import EpicsSignal
from ...component import Component

logger = logging.getLogger(__name__)


class EpicsSignalWithRBV(base.EpicsSignalWithRBV, EpicsSignal):
    pass


class ADComponent(base.ADComponent, Component):
    pass


class ADBase(base.ADBase, Device):
    def stage(self, *args, **kwargs):
        ret = Device.stage(self, *args, **kwargs)
        try:
            self.validate_asyn_ports()
        except RuntimeError as err:
            self.unstage(*args, **kwargs)
            raise err
        return ret 

