"""
Module for the SXR Test Absorbers.
"""
from __future__ import annotations

from ophyd.device import Component as Cpt

from .digital_signals import J120K
from .epics_motor import BeckhoffAxisNoOffset
from .inout import TwinCATInOutPositioner
from .interface import BaseInterface, LightpathInOutCptMixin
from .signal import PytmcSignal


class ST3K4AutoError(RuntimeError):
    ...


class SxrTestAbsorberStates(TwinCATInOutPositioner):
    """
    SXR Test absorber states

    This has some automation where it tracks the position of ST3K4.
    Accordingly, it has a configuration parameter for enabling/disabling this.
    """

    st3k4_auto = Cpt(PytmcSignal, ':ST3K4_AUTO', io='io', kind='config')


class SxrTestAbsorber(BaseInterface, LightpathInOutCptMixin):
    """
    SXR Test Absorber: Used for testing the sxr beamline at high pulse rates.

    This device has 1 main member: the stopper/absorber (diamond stopper).

    The vertical motor moves stopper in and out of the beam path in
    the +/- y direction.

    It has a state selector that can be used to move in and out by state name.

    Instantiate me with:
    st1k4 = SxrTestAbsorber("ST1K4:TEST", name="st1k4")
    """

    tab_component_names = True

    state = Cpt(SxrTestAbsorberStates, ':MMS:STATE', kind='hinted')
    absorber_vert = Cpt(BeckhoffAxisNoOffset, ':MMS:01', kind='normal')
    flow_switch = Cpt(J120K, '', kind='normal',
                      doc='Device that indicates nominal PCW Flow Rate.')

    lightpath_cpts = ['state']
