#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulated RVC300 controller
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
from .component import Component
from .signal import FakeSignal
from ..epics import rvc300

logger = logging.getLogger(__name__)


class RVC300(rvc300.RVC300):
    """
    Base RVC300 Class
    """
    # Configuration
    measurements = Component(FakeSignal)
    configvars = Component(FakeSignal)

    # Pressure Readback
    pressure = Component(FakeSignal)

    # System Control
    operating_mode = Component(FakeSignal)
    pressure_setpoint = Component(FakeSignal)
    flow_setpoint = Component(FakeSignal)
    close_valve = Component(FakeSignal)

    # Valve Information
    valve_type = Component(FakeSignal)
    valve_version = Component(FakeSignal)
    valve_temperature = Component(FakeSignal)
    valve_position = Component(FakeSignal)
    valve_status = Component(FakeSignal)
    
    # PID
    controller_type = Component(FakeSignal)
    pcomp = Component(FakeSignal)
    manipvar = Component(FakeSignal)
    icomp = Component(FakeSignal)
    dcomp = Component(FakeSignal)
    p_gain = Component(FakeSignal)
    reset_time = Component(FakeSignal)
    derivative_time = Component(FakeSignal)

    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        
        self.pressure._get_readback = lambda : self.pressure_readback()

    def pressure_readback(self):
        if self.mode == "FLOW":
            return self.flow_setpoint.value * 10
        else:
            return self.pressure_setpoint.value
