from ophyd import Device, Signal, Component as Cpt

from .inout import InOutPositioner
from .interface import BaseInterface, LightpathInOutMixin
from .signal import PytmcSignal


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


class RTDSBase(BaseInterface, Device, LightpathInOutMixin):
    """Rapid Turnaround Diagnostic Station."""
    lightpath_cpts = ['mpa1', 'mpa2', 'mpa3', 'mpa4']
    _lightpath_mixin = True

    _icon = 'fa.stop-circle'

    mpa1 = Cpt(PneumaticActuator, ':MPA:01', kind='normal')
    mpa2 = Cpt(PneumaticActuator, ':MPA:02', kind='normal')
    mpa3 = Cpt(PneumaticActuator, ':MPA:03', kind='normal')
    mpa4 = Cpt(PneumaticActuator, ':MPA:04', kind='normal')


class RTDSL0(RTDSBase):
    """RTDS Configuration on the HXR Line."""
    lightpath_cpts = ['mpa1', 'mpa2', 'mpa3']

    mpa4 = None


class RTDSK0(RTDSBase):
    """RTDS Configuration on the SXR Line."""
    pass
