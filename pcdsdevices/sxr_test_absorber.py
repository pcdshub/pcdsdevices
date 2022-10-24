"""
Module for the SXR Test Absorbers.
"""
from lightpath import LightpathState
from ophyd.device import Component as Cpt

from .epics_motor import BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathMixin


class SxrTestAbsorber(BaseInterface, LightpathMixin):
    """
    SXR Test Absorber: Used for testing the sxr beamline at high pulse rates.

    This device has 1 main members: the stopper/absorber (diamond stopper).

    The vertical motor moves stopper in and out of the beam path in
    the +/- y direction.
    """

    tab_component_names = True

    absorber_vert = Cpt(BeckhoffAxisNoOffset, ':MMS:01', kind='normal')

    lightpath_cpts = ['absorber_vert.user_readback']

    def calc_lightpath_state(self, absorber_vert: float) -> LightpathState:
        pos = absorber_vert
        # 0 is out, negative is in
        # this device has never been inserted, so we don't know the in pos
        self._inserted = pos < -1
        self._removed = pos > -1
        self._transmission = int(self._removed)

        return LightpathState(
            inserted=self._inserted,
            removed=self._removed,
            output={self.output_branches[0]: self._transmission}
        )
