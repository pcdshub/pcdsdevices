"""
Module for the various absorbers.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device

from .epics_motor import BeckhoffAxis

# from ophyd.device import FormattedComponent as FCpt

# from .interface import BaseInterface


class TestAbsorber(Device):
    """
    SXR Test Absorber: Used for testing the sxr beamline at high pulse rates.

    This device has 1 main members: the stopper/absorber (diamond stopper).

    The vertical motor moves stopper in and out of the beam path in
    the +/- y direction.
    """

    tab_component_names = True

    absorber_vert = Cpt(BeckhoffAxis, ':absorber_vert', kind='normal')
