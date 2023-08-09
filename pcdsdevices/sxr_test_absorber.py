"""
Module for the SXR Test Absorbers.
"""
from ophyd.device import Component as Cpt

from .epics_motor import BeckhoffAxisNoOffset
from .inout import TwinCATInOutPositioner
from .interface import BaseInterface, LightpathInOutCptMixin


class SxrTestAbsorber(BaseInterface, LightpathInOutCptMixin):
    """
    SXR Test Absorber: Used for testing the sxr beamline at high pulse rates.

    This device has 1 main member: the stopper/absorber (diamond stopper).

    The vertical motor moves stopper in and out of the beam path in
    the +/- y direction.

    It has a state selector that can be used to move in and out by state name.
    """

    tab_component_names = True

    state = Cpt(TwinCATInOutPositioner, ':MMS:STATE', kind='hinted')
    absorber_vert = Cpt(BeckhoffAxisNoOffset, ':MMS:01', kind='normal')

    lightpath_cpts = ['state']
