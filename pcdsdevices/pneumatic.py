"""
Pneumatic Classes.

This Module contains all the classes relating to Pneumatic Actuators
"""

from lightpath import LightpathState
from ophyd import Component as Cpt
from ophyd import EpicsSignal, EpicsSignalRO
from ophyd.status import Status

from pcdsdevices.interface import BaseInterface, LightpathMixin


class BeckhoffPneumatic(BaseInterface, LightpathMixin):
    """
    Class containing basic Beckhoff Pneumatic support
    """
    lightpath_cpts = ['limit_switch_in', 'limit_switch_out']

    # readouts
    limit_switch_in = Cpt(EpicsSignalRO, ':PLC:bInLimitSwitch')
    limit_switch_out = Cpt(EpicsSignalRO, ':PLC:bOutLimitSwitch')

    retract_status = Cpt(EpicsSignalRO, ':bRetractDigitalOutput')
    insert_status = Cpt(EpicsSignalRO, ':bInsertDigitalOutput')

    # logic and supervisory
    interlock_ok = Cpt(EpicsSignalRO, 'bInterlockOK')
    insert_ok = Cpt(EpicsSignalRO, 'bInsertEnable')
    retract_ok = Cpt(EpicsSignalRO, 'bretractEnable')

    # commands
    insert_signal = Cpt(EpicsSignal, 'CMD:IN')
    retract_signal = Cpt(EpicsSignal, 'CMD:OUT')

    # returns
    busy = Cpt(EpicsSignalRO, ':bBusy')
    done = Cpt(EpicsSignalRO, ':bDone')
    reset = Cpt(EpicsSignal, ':bReset')
    error = Cpt(EpicsSignalRO, ':PLC:bError')
    error_id = Cpt(EpicsSignalRO, ':PLC:nErrorId')
    error_message = Cpt(EpicsSignalRO, ':PLC:sErrorMessage')
    position_state = Cpt(EpicsSignalRO, ':nPositionState', kind='hinted')

    def insert(self, wait: bool = False, timeout: float = 10.0) -> Status:
        """
        Method for inserting Beckhoff Pneumatic Actuator
        """
        status = Status(self, timeout)

        def callback(value):
            if value:
                if self.error.get():
                    error = Exception(self.error_message.get())
                    status.set_exception(error)
                else:
                    status.set_finished()
                    self.done.clear_sub(callback)

        self.done.subscribe(callback)

        if self.insert_ok.get():
            self.insert_signal.put(1)
        else:
            error = Exception("Insertion not permitted by PLC")
            status.set_exception(error)

        if wait:
            status.wait()
        return status

    def remove(self):
        if self.retract_ok.get():
            self.retract_signal.put(1)
        else:
            raise RuntimeError("Removal not permitted by PLC")

    def calc_lightpath_state(self, limit_switch_in=None, limit_switch_out=None):
        trans = 0.0 if limit_switch_in and not limit_switch_out else 1.0

        status = LightpathState(
            inserted=bool(limit_switch_in),
            removed=bool(limit_switch_out),
            output={self.output_branches[0]: trans}
        )
        return status
