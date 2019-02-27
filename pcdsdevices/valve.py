"""
Standard classes for LCLS Gate Valves
"""
import logging
from enum import Enum

from ophyd import EpicsSignal, EpicsSignalRO, Component as Cpt, Device

from .inout import InOutPositioner, InOutPVStatePositioner

logger = logging.getLogger(__name__)


class Commands(Enum):
    """
    Command aliases for opening and closing valves
    """
    close_valve = 0
    open_valve = 1


class InterlockError(PermissionError):
    """
    Error when request is blocked by interlock logic
    """
    pass


class Stopper(InOutPVStatePositioner):
    """
    Controls Stopper

    A base class for a device with two limits switches controlled via an
    external command PV. This fully encompasses the controls `Stopper`
    installations as well as un-interlocked `GateValves`

    Parameters
    ----------
    prefix : ``str``
        Full PPS Stopper PV

    name : ``str``
        Alias for the stopper

    Attributes
    ----------
    commands : ``Enum``
        An enum with integer values for ``open_valve``, ``close_valve`` values
    """
    # Limit-based states
    open_limit = Cpt(EpicsSignalRO, ':OPEN', kind='normal')
    closed_limit = Cpt(EpicsSignalRO, ':CLOSE', kind='normal')

    # Information on device control
    command = Cpt(EpicsSignal, ':CMD', kind='omitted')
    commands = Commands

    _state_logic = {'open_limit': {0: 'defer',
                                   1: 'OUT'},
                    'closed_limit': {0: 'defer',
                                     1: 'IN'}}
    # QIcon for UX
    _icon = 'fa.times-circle'

    tab_whitelist = ['open', 'close']

    def _do_move(self, state):
        if state.name == 'IN':
            self.command.put(self.commands.close_valve.value)
        elif state.name == 'OUT':
            self.command.put(self.commands.open_valve.value)

    def open(self, **kwargs):
        """
        Open the stopper
        """
        return self.remove(**kwargs)

    def close(self, **kwargs):
        """
        Close the stopper
        """
        return self.insert(**kwargs)


class GateValve(Stopper):
    """
    Basic Vacuum Valve

    This inherits directly from :class:`.Stopper` but adds additional logic to
    check the state of the interlock before requesting motion. This is not a
    safety feature, just a notice to the operator.
    """
    # Limit based states
    open_limit = Cpt(EpicsSignalRO, ':OPN_DI', kind='normal')
    closed_limit = Cpt(EpicsSignalRO, ':CLS_DI', kind='normal')

    # Commands and Interlock information
    command = Cpt(EpicsSignal,   ':OPN_SW', kind='omitted')
    interlock = Cpt(EpicsSignalRO, ':OPN_OK', kind='normal')

    # QIcon for UX
    _icon = 'fa.hourglass'

    tab_whitelist = ['interlocked']

    def check_value(self, value):
        """Check when removing GateValve interlock is off"""
        value = super().check_value(value)
        if value == self.states_enum.OUT and self.interlocked:
            raise InterlockError('Valve is currently forced closed')
        return value

    @property
    def interlocked(self):
        """
        Whether the interlock on the valve is active, preventing the valve from
        opening
        """
        return not bool(self.interlock.get())


class PPSStopper(InOutPositioner):
    """
    PPS Stopper

    Control of this device only available to PPS systems. This class merely
    interprets the summary of limit switches to let the controls system know
    the current position.

    Because naming conventions for the states are non-uniform this class allows
    you to enter the values at initialization.

    Parameters
    ----------
    prefix : ``str``
        Full PPS Stopper PV

    name : ``str``
        Alias for the stopper

    in_state : ``str``, optional
        String associatted with in enum value

    out_state : ``str``, optional
        String associatted with out enum value
    """
    state = Cpt(EpicsSignalRO, '', string=True, kind='hinted')
    # QIcon for UX
    _icon = 'fa.times-circle'

    def __init__(self, prefix, *, in_state='IN', out_state='OUT', **kwargs):
        # Store state information
        self.in_states = [in_state]
        self.out_states = [out_state]
        self.states_list = self.in_states + self.out_states
        # Load InOutPositioner
        super().__init__(prefix, **kwargs)

    def check_value(self, state):
        """
        PPSStopper can not be commanded via EPICS
        """
        raise PermissionError("PPSStopper can not be commanded via EPICS")


class VCN(Device):
    position_readback = Cpt(EpicsSignalRO, ':POS_RDBK', kind='hinted',
                            doc='Valve position readback')
    position_control = Cpt(EpicsSignal, ':POS_CTRL', kind='normal',
                           doc='Requested position to control the valve')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK', kind='normal',
                       doc='Interlock ok status')
    open_command = Cpt(EpicsSignal, ':OPN_SW', kind='normal',
                       doc='Epics command to open valve')
    position_output = Cpt(EpicsSignalRO, ':POS_DES', kind='omitted',
                          doc='requested position set to output channel')
    state = Cpt(EpicsSignalRO, ':STATE', kind='hinted', doc='Valve state')


class VCC_NO(Device):
    close_command = Cpt(EpicsSignal, ':CLS_SW', kind='normal',
                        doc='Epics command to close valve')
    close_override = Cpt(EpicsSignal, ':FORCE_CLS', kind='omitted',
                         doc='Epics command to close the vale in '
                             'override mode')
    override_on = Cpt(EpicsSignal, ':OVRD_ON', kind='omitted',
                      doc='Epics command to set/reset override mode')
    close_ok = Cpt(EpicsSignalRO, ':CLS_OK', kind='normal',
                   doc='Used for normally open valves')
    close_do = Cpt(EpicsSignalRO, ':CLS_DO', kind='normal',
                   doc='PLC output to close valve')


class VVC(Device):
    open_command = Cpt(EpicsSignal, ':OPN_SW', kind='normal',
                       doc='Epics command to open valve')
    open_ok = Cpt(EpicsSignalRO, ':OPN_OK', kind='normal',
                  doc='Valve is OK to open interlock')
    override_on = Cpt(EpicsSignal, ':OVRD_ON', kind='omitted',
                      doc='Epics command to set/reset override mode')
    open_override = Cpt(EpicsSignal, ':FORCE_OPN', kind='omitted',
                        doc='Epics command to open the valve in override mode')
    open_do = Cpt(EpicsSignalRO, ':OPN_DO', kind='normal',
                  doc='PLC output to open valve')


class VRC(VVC):
    open_di = Cpt(EpicsSignalRO, ':OPN_DI', kind='hinted',
                  doc='Open limit switch digital input')
    cls_di = Cpt(EpicsSignalRO, ':CLS_DI', kind='hinted',
                 doc='Closed limit switch digital input')
    state = Cpt(EpicsSignalRO, ':STATE', kind='normal', doc='Valve state')


class VGC(VRC):
    diff_press_ok = Cpt(EpicsSignalRO, ':DP_OK', kind='normal',
                        doc='Differential pressure interlock ok')
    ext_ilk_ok = Cpt(EpicsSignalRO, ':Ext_ILK_OK', kind='normal',
                     doc='External interlock ok')
    at_vac_sp = Cpt(EpicsSignal, ':AT_VAC_SP', kind='config',
                    doc='AT VAC set point value')
    at_vac_hysterisis = Cpt(EpicsSignal, ':AT_VAC_HYS', kind='config',
                            doc='AT VAC hysterisis')
    at_vac = Cpt(EpicsSignalRO, ':AT_VAC', kind='normal',
                 doc='At vacuum set point is reached')
    error = Cpt(EpicsSignalRO, ':Error', kind='normal',
                doc='Error present')


class Gauge(Device):
    pressure = Cpt(EpicsSignalRO, ':PRESS', kind='hinted',
                   doc='Gauge pressure reading')
    gauge_at_vac = Cpt(EpicsSignalRO, ':AT_VAC', kind='normal',
                       doc='Gauge is at VAC')
    pressure_ok = Cpt(EpicsSignalRO, ':PRESS_OK', kind='normal',
                      doc='Pressure reading ok')
    at_vac_setpoint = Cpt(EpicsSignal, ':VAC_SP', kind='config',
                          doc='At vacuum setpoint for all gauges')
    state = Cpt(EpicsSignalRO, ':STATE', kind='hinted',
                doc='state of the gauge')


class GCC(Gauge):
    """
    Cold Cathode Gauge

    Class to facilitate cold cathod gauge controls and readback on our Beckhoff
    PLCs. Controlled using the ADS driver using records from pytmc.
    """
    high_voltage_on = Cpt(EpicsSignal, ':HV_SW', kind='normal',
                          doc='Command to switch the high voltage on')
    high_voltage_disable = Cpt(EpicsSignalRO, ':HV_DIS', kind='normal',
                               doc='Enables the high voltage on the cold '
                                   'cathode gauge')
    protection_setpoint = Cpt(EpicsSignalRO, ':PRO_SP', kind='normal',
                              doc='Protection setpoint for ion gauges at '
                                  'which the gauge turns off')
    setpoint_hysterisis = Cpt(EpicsSignal, ':SP_HYS', kind='config',
                              doc='Protection setpoint hysterisis')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK', kind='normal',
                       doc='Interlock is OK')


class GCC500(GCC):
    high_voltage_is_on = Cpt(EpicsSignalRO, ':HV_ON', kind='normal',
                             doc='State of the HV')
    disc_active = Cpt(EpicsSignalRO, ':DISC_ACTIVE', kind='normal',
                      doc='Discharge current active')


class GPI(GCC500):
    pass


class PIP(Device):
    pressure = Cpt(EpicsSignalRO, ':PRESS', kind='hinted',
                   doc='Pressure reading')
    high_voltage_do = Cpt(EpicsSignalRO, ':HV_DO', kind='normal',
                          doc='High voltage digital output')
    high_voltage_switch = Cpt(EpicsSignal, ':HV_SW', kind='omitted',
                              doc='Epics command to switch on the '
                                  'high voltage')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK', kind='normal',
                       doc='Interlock is ok when true')
    at_vac_sp = Cpt(EpicsSignal, ':AT_VAC_SP', kind='omitted',
                    doc='At vacuum setpoint')
    set_point_relay = Cpt(EpicsSignalRO, ':SP_DI', kind='normal',
                          doc='Set point digital input relay')


class PTM(Device):
    run_sw = Cpt(EpicsSignalRO, ':RUN_SW', kind='omitted')
    rst_sw = Cpt(EpicsSignalRO, ':RST_SW', kind='normal')
    run_do = Cpt(EpicsSignalRO, ':RUN_DO', kind='normal')
    run_ok = Cpt(EpicsSignalRO, ':RUN_OK', kind='omitted')
    at_spd = Cpt(EpicsSignalRO, ':AT_SPD', kind='omitted')
    accel = Cpt(EpicsSignalRO, ':ACCEL', kind='normal')
    speed = Cpt(EpicsSignalRO, ':SPEED', kind='normal')
    fault = Cpt(EpicsSignalRO, ':FAULT', kind='normal')
    warn = Cpt(EpicsSignalRO, ':WARN', kind='normal')
    alarm = Cpt(EpicsSignalRO, ':ALARM', kind='normal')
    backing_pressure_sp = Cpt(EpicsSignalRO, ':BackingPressureSP',
                              kind='omitted')
    inlet_pressure_sp = Cpt(EpicsSignalRO, ':InletPressureSP', kind='omitted')
