from lightpath import LightpathState
from ophyd import Component as Cpt
from ophyd import Signal

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .inout import InOutPositioner
from .interface import BaseInterface, LightpathInOutCptMixin, LightpathMixin
from .signal import EpicsSignalRO, PytmcSignal


class PneumaticActuator(InOutPositioner):
    states_list = ['RETRACTED', 'INSERTED', 'MOVING', 'INVALID']
    in_states = ['INSERTED']
    out_states = ['RETRACTED']
    _invalid_states = ['MOVING', 'INVALID']
    _unknown = False

    state = Cpt(PytmcSignal, ':POS_STATE', io='i', kind='hinted')

    in_sw = Cpt(PytmcSignal, ':IN', io='i', kind='normal')
    out_sw = Cpt(PytmcSignal, ':OUT', io='i', kind='normal')
    error = Cpt(PytmcSignal, ':ERROR', io='i', kind='normal')

    in_cmd = Cpt(PytmcSignal, ':IN_CMD', io='io', kind='config')
    out_cmd = Cpt(PytmcSignal, ':OUT_CMD', io='io', kind='config')
    filter_type = Cpt(Signal, value='Unknown filter', kind='config')

    done = Cpt(PytmcSignal, ':MOT_DONE', io='i', kind='omitted')

    def __init__(self, prefix, *, name, transmission=1,
                 filter_type='Unknown filter', **kwargs):
        self._transmission = {'INSERTED': transmission}
        super().__init__(prefix, name=name, **kwargs)
        self.filter_type.put(filter_type)

    def _do_move(self, state):
        """
        Override state move because we can't use the default.

        Here we need to put 1 to the proper command pv.
        """
        if state.name == 'INSERTED':
            self.in_cmd.put(1)
        elif state.name == 'RETRACTED':
            self.out_cmd.put(1)


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
