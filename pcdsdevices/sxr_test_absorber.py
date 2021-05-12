"""
Module for the SXR Test Absorbers.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device

from .epics_motor import BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathMixin


class SxrTestAbsorber(BaseInterface, LightpathMixin, Device):
    """
    SXR Test Absorber: Used for testing the sxr beamline at high pulse rates.

    This device has 1 main members: the stopper/absorber (diamond stopper).

    The vertical motor moves stopper in and out of the beam path in
    the +/- y direction.
    """

    tab_component_names = True

    absorber_vert = Cpt(BeckhoffAxisNoOffset, ':MMS:01', kind='normal')

    lightpath_cpts = ['absorber_vert']

    def _set_lightpath_states(self, lightpath_values):
        pos = lightpath_values[self.absorber_vert]['value']
        # 0 is out, negative is in
        # this device has never been inserted, so we don't know the in pos
        self._inserted = pos < -1
        self._removed = pos > -1
        self._transmission = int(self._removed)
