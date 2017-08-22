#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standard classes for LCLS Gate Valves
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
from ophyd.positioner import PositionerBase
from ophyd.status import wait as status_wait
from ophyd.utils.epics_pvs import raise_if_disconnected

##########
# Module #
##########
from ..epics import (valve, state)
from .signal import FakeSignal
from .component import (FormattedComponent, Component)

ValveLimits = state.pvstate_class('ValveLimits',
                                  {'open_limit': {'pvname': ':OPN_DI',
                                                  0: 'defer',
                                                  1: 'out'},
                                   'closed_limit': {'pvname': ':CLS_DI',
                                                    0: 'defer',
                                                    1: 'in'}},
                                  doc='State description of valve limits',
                                  signal_class=FakeSignal)

class ValveBase(valve.ValveBase):
    """
    Base class for the valve simulated device.
    """
    # Simulated components
    command = Component(FakeSignal)
    interlock = Component(FakeSignal, value=0)
    limits = Component(ValveLimits, "")
    
class PositionValve(valve.PositionValve, ValveBase):
    """
    Simulated valve that has a position component.
    """
    pos = Component(FakeSignal, ":POSITION")

    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        self.pos._get_readback = lambda : self.command.value


class BypassValve(valve.BypassValve, ValveBase):
    """
    Simulated valve that has the bypass component.
    """
    bypass_mode = Component(FakeSignal, ":BYPASS")


class OverrideValve(valve.OverrideValve, ValveBase):
    """
    Simulated valve that has the override component.
    """
    override_mode = Component(FakeSignal, ":OVERRIDE")


class N2CutoffValve(valve.N2CutoffValve, OverrideValve):
    """
    Nitrogen Cutoff Valve
    """
    pass

class ApertureValve(valve.ApertureValve, PositionValve, BypassValve):
    """
    Aperture Valve
    """
    pass

class ReadbackValve(valve.ReadbackValve, PositionValve, OverrideValve):
    """
    Readback Valve
    """
    pass

