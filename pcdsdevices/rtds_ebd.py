from lightpath import LightpathState
from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface, LightpathInOutCptMixin, LightpathMixin
from .pneumatic import PneumaticActuator
from .signal import EpicsSignalRO


class RTDSX0ThreeStage(BaseInterface, LightpathMixin):
    """Three stages X,Y,Z, for solid drilling experiments"""

    mmsx = Cpt(BeckhoffAxis, ':MMS:X', kind='normal')
    mmsy = Cpt(BeckhoffAxis, ':MMS:Y', kind='normal')
    mmsz = Cpt(BeckhoffAxis, ':MMS:Z', kind='normal')

    # Determine if the y stage is at it's outer limit switch
    open_limit = Cpt(EpicsSignalRO, ':MMS:Y.HLS', kind='normal',
                     doc='Reads if the y-stage is at its outer limit.')
    lightpath_cpts = ['open_limit']

    def calc_lightpath_state(self, open_limit=None):
        # Logic, calculations using open_limit for y-stage
        status = LightpathState(
            inserted=not open_limit, removed=open_limit,
            output={'K0' : 0.0}
        )
        return status


class RTDSBase(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    """Rapid Turnaround Diagnostic Station."""
    lightpath_cpts = ['mpa1', 'mpa2', 'mpa3', 'mpa4']

    _icon = 'fa.stop-circle'

    mpa1 = Cpt(PneumaticActuator, ':MPA:01', kind='normal')
    mpa2 = Cpt(PneumaticActuator, ':MPA:02', kind='normal')
    mpa3 = Cpt(PneumaticActuator, ':MPA:03', kind='normal')
    mpa4 = Cpt(PneumaticActuator, ':MPA:04', kind='normal')


class RTDSL0(RTDSBase):
    """
    RTDS Configuration on the HXR Line.

    mpa4 is an available but unused channel, showing invalid data.
    """
    lightpath_cpts = ['mpa1', 'mpa2', 'mpa3']

    mpa4 = None


class RTDSK0(RTDSBase):
    """
    RTDS Configuration on the SXR Line.

    mpa3 and mpa4 are available but unused channels, showing invalid data.
    """
    lightpath_cpts = ['mpa1', 'mpa2']

    mpa3 = None
    mpa4 = None
