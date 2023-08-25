"""
Module for the SXR Test Absorbers.
"""
from __future__ import annotations

from typing import Callable

from ophyd.device import Component as Cpt

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

    def set(
        self,
        position: str | int,
        moved_cb: Callable | None = None,
        timeout: float | None = None,
    ):
        if self.st3k4_auto.get():
            raise ST3K4AutoError(
                "ST1K4 must follow ST3K4. Move rejected."
            )
        return super().set(position, moved_cb=moved_cb, timeout=timeout)


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

    lightpath_cpts = ['state']
