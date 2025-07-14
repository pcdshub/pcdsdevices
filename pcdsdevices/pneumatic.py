"""
Pneumatic Classes.

This Module contains all the classes relating to Pneumatic Actuators
"""

from lightpath import LightpathState
from ophyd import Component as Cpt
from ophyd import Signal
from ophyd.status import Status

from pcdsdevices.interface import BaseInterface, LightpathMixin

from .analog_signals import FDQ
from .inout import InOutPositioner
from .signal import PytmcSignal


class BeckhoffPneumatic(BaseInterface, LightpathMixin):
    """
    Class containing basic Beckhoff Pneumatic support
    """
    lightpath_cpts = ['limit_switch_in', 'limit_switch_out']

    # readouts
    limit_switch_in = Cpt(PytmcSignal, ':PLC:bInLimitSwitch', io="i")
    limit_switch_out = Cpt(PytmcSignal, ':PLC:bOutLimitSwitch', io="i")

    retract_status = Cpt(PytmcSignal, ':bRetractDigitalOutput', io="i")
    insert_status = Cpt(PytmcSignal, ':bInsertDigitalOutput', io="i")

    # logic and supervisory
    interlock_ok = Cpt(PytmcSignal, ':bInterlockOK', io="i")
    insert_ok = Cpt(PytmcSignal, ':bInsertEnable', io="i")
    retract_ok = Cpt(PytmcSignal, ':bRetractEnable', io="i")

    # commands
    insert_signal = Cpt(PytmcSignal, ':CMD:IN', io="io")
    retract_signal = Cpt(PytmcSignal, ':CMD:OUT', io="io")

    # returns
    busy = Cpt(PytmcSignal, ':bBusy', io="i")
    done = Cpt(PytmcSignal, ':bDone', io="i")
    reset = Cpt(PytmcSignal, ':bReset', io="io")
    error = Cpt(PytmcSignal, ':PLC:bError', io="i")
    error_id = Cpt(PytmcSignal, ':PLC:nErrorId', io="i")
    error_message = Cpt(PytmcSignal, ':PLC:sErrorMessage', io="i", string=True)
    position_state = Cpt(PytmcSignal, ':nPositionState', kind='hinted', io="i")

    def callback(self, *, old_value, value, **kwargs):
        if value:
            self.done.clear_sub(self.callback)
            if self.error.get():
                error = Exception(self.error_message.get())
                self.status.set_exception(error)
            else:
                self.status.set_finished()

    def insert(self, wait: bool = False, timeout: float = 10.0) -> Status:
        """
        Method for inserting Beckhoff Pneumatic Actuator
        """
        self.status = Status(timeout)

        if self.insert_ok.get():
            self.done.subscribe(self.callback)
            self.insert_signal.put(1)
        else:
            error = Exception("Insertion not permitted by PLC")
            self.status.set_exception(error)

        if wait:
            self.status.wait()
        return self.status

    def remove(self, wait: bool = False, timeout: float = 10.0) -> Status:
        """
        Method for removing Beckhoff Pneumatic Actuator
        """
        self.status = Status(timeout)

        if self.retract_ok.get():
            self.done.subscribe(self.callback)
            self.retract_signal.put(1)
        else:
            error = Exception("Removal not permitted by PLC")
            self.status.set_exception(error)

        if wait:
            self.status.wait()
        return self.status

    def calc_lightpath_state(self, limit_switch_in=None, limit_switch_out=None):
        trans = 0.0 if limit_switch_in and not limit_switch_out else 1.0

        status = LightpathState(
            inserted=bool(limit_switch_in),
            removed=bool(limit_switch_out),
            output={self.output_branches[0]: trans}
        )
        return status


class BeckhoffPneumaticFDQ(BeckhoffPneumatic):
    """
    Beckhoff Pneumatics with a flow meter for cooling readback.
    """
    flow_meter = Cpt(FDQ, '', kind='normal',
                     doc='Device that measures PCW Flow Rate.')


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
