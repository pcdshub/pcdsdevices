#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes for simulated gauges
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############

##########
# Module #
##########
from .signal import FakeSignal
from .component import (Component, FormattedComponent)
from ..epics import gauge

logger = logging.getLogger(__name__)


class GaugeBase(gauge.GaugeBase):
    """
    Simulated base gauge class.
    """
    pressure = Component(FakeSignal)
    status = Component(FakeSignal)

    
class Pirani(gauge.Pirani, GaugeBase):
    """
    Simulated pirani gauge.
    """
    pass


class ColdCathode(gauge.ColdCathode, GaugeBase):
    """
    Simulated cold cathode class.
    """
    pirani = FormattedComponent(Pirani, "{self._prefix_pirani}")
