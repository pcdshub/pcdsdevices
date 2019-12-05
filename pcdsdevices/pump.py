"""
Standard classes for LCLS Pumps
"""
import logging

from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV, Device
from ophyd import Component as Cpt, FormattedComponent as FCpt

from .doc_stubs import IonPump_base
from .interface import BaseInterface

logger = logging.getLogger(__name__)


class TurboPump(Device, BaseInterface):
    """
    Vacuum Pump
    """
    atspeed = Cpt(EpicsSignal, ':ATSPEED_DI', kind='normal')
    start = Cpt(EpicsSignal, ':START_SW', kind='normal')

    tab_whitelist = ['run', 'stop', 'atspeed']

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)


class EbaraPump(Device, BaseInterface):
    """
    Ebara Turbo Pump
    """
    start = Cpt(EpicsSignal, ':MPSTART_SW', kind='normal')

    tab_whitelist = ['run', 'stop']

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)


class GammaController(Device, BaseInterface):
    """
    Ion Pump Gamma controller
    """
    channel1name = Cpt(EpicsSignal, ':CHAN1NAME', kind='config')
    channel2name = Cpt(EpicsSignal, ':CHAN2NAME', kind='config')
    model = Cpt(EpicsSignalRO, ':MODEL', kind='config')
    firmwareversion = Cpt(EpicsSignalRO, ':FWVERSION', kind='config')
    linevoltage = Cpt(EpicsSignalRO, ':LINEV', kind='omitted')
    linefrequency = Cpt(EpicsSignalRO, ':LINEFREQ', kind='omitted')
    cooling_fan_status = Cpt(EpicsSignalRO, ':FAN', kind='omitted')

    power_autosave = Cpt(EpicsSignal, ':ASPOWERE', write_pv=':ASPOWEREDES',
                         kind='config')
    high_voltage_enable_autosave = Cpt(EpicsSignal, ':ASHVE',
                                       write_pv=':ASHVEDES', kind='normal')

    unit = Cpt(EpicsSignal, ':PEGUDES', kind='normal')

    tab_component_names = True


class IonPumpBase(Device, BaseInterface):
    """
%s
    """
    __doc__ = (__doc__ % IonPump_base).replace('Ion Pump',
                                               'Ion Pump Base Class')

    _pressure = Cpt(EpicsSignalRO, ':PMON', kind='hinted')
    _egu = Cpt(EpicsSignalRO, ':PMON.EGU', kind='omitted')
    current = Cpt(EpicsSignalRO, ':IMON', kind='normal')
    voltage = Cpt(EpicsSignalRO, ':VMON', kind='normal')
    status_code = Cpt(EpicsSignalRO, ':STATUSCODE', kind='normal', string=True)
    status = Cpt(EpicsSignalRO, ':STATUS', kind='normal')
    # check if this work as its an enum
    state = Cpt(EpicsSignal, ':STATEMON', write_pv=':STATEDES', kind='normal',
                string=True)
    # state_cmd = Cpt(EpicsSignal, ':STATEDES', kind='normal')

    pumpsize = Cpt(EpicsSignal, ':PUMPSIZEDES', write_pv=':PUMPSIZE',
                   kind='omitted')
    controllername = Cpt(EpicsSignal, ':VPCNAME', kind='omitted')
    hvstrapping = Cpt(EpicsSignal, ':VDESRBCK', kind='omitted')
    supplysize = Cpt(EpicsSignalRO, ':SUPPLYSIZE', kind='omitted')

    aomode = Cpt(EpicsSignal, ':AOMODEDES', write_pv=':AOMODE', kind='config')
    calfactor = Cpt(EpicsSignal, ':CALFACTORDES', write_pv=':CALFACTOR',
                    kind='config')

    tab_whitelist = ['on', 'off', 'info', 'pressure']
    tab_component_names = True

    def on(self):
        self.state.put(1)

    def off(self):
        self.state.put(0)

    def info(self):
        outString = (
            '%s is an ion pump with base PV %s which is %s \n' %
            (self.name, self.prefix, self.state.get()))
        if self.state.get() == 'ON':
            outString += 'Pressure: %g \n' % self.pressure()
            outString += 'Current: %g \n' % self.current.get()
            outString += 'Voltage: %g' % self.voltage.get()
        return outString

    def pressure(self):
        if self.state.get() == 'ON':
            return self._pressure.get()
        else:
            return -1.

    def egu(self):
        return self._egu.get()


class IonPumpWithController(IonPumpBase):
    """
%s

    prefix_controller : ``str``
        Ion Pump Controller base PV

    """
    __doc__ = (__doc__ % IonPump_base).replace('Pump', 'Pump w/ controller')

    controller = FCpt(GammaController, '{self.prefix_controller}')

    tab_component_names = True

    def __init__(self, prefix, *, prefix_controller, **kwargs):
        # base PV for ion pump controller
        self.prefix_controller = prefix_controller
        # Load Ion Pump itself
        super().__init__(prefix, **kwargs)

    def egu(self):
        return self.controller.unit.get()


class PIPPLC(Device):
    """
    Class for PLC-controlled Ion Pumps

    Newer class. This and below are still missing some functionality.
    Still need to work out replacement of old classes.
    """
    pressure = Cpt(EpicsSignalRO, ':PRESS_RBV', kind='hinted',
        doc='pressure reading')
    high_voltage_do = Cpt(EpicsSignalRO, ':HV_DO_RBV', kind='normal',
        doc='high voltage digital output')
    high_voltage_switch = Cpt(EpicsSignalWithRBV, ':HV_SW', kind='omitted',
        doc='epics command to witch on the high voltage')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
        doc='interlock  is ok when true')
    at_vac_sp = Cpt(EpicsSignalWithRBV, ':AT_VAC_SP', kind='omitted',
        doc='at vacuum set point')
    set_point_relay = Cpt(EpicsSignalRO, ':SP_DI_RBV', kind='normal',
        doc='set point digital input relay')


class PTMPLC(Device):
    """
    Class for PLC-controlled Turbo Pump

    """
    switch_pump_on = Cpt(EpicsSignalWithRBV, ':RUN_SW', kind='omitted',
        doc='')
    reset_fault = Cpt(EpicsSignalWithRBV, ':RST_SW', kind='normal', doc='')
    run_do = Cpt(EpicsSignalRO, ':RUN_DO_RBV', kind='normal', doc='')
    run_ok = Cpt(EpicsSignalRO, ':RUN_OK_RBV', kind='omitted', doc='')
    pump_at_speed = Cpt(EpicsSignalRO, ':AT_SPD_RBV', kind='omitted',
        doc='')
    pump_accelerating = Cpt(EpicsSignalRO, ':ACCEL_RBV', kind='normal',
        doc='')
    pump_speed = Cpt(EpicsSignalRO, ':SPEED_RBV', kind='normal', doc='')
    fault = Cpt(EpicsSignalRO, ':FAULT_RBV', kind='normal', doc='')
    warn = Cpt(EpicsSignalRO, ':WARN_RBV', kind='normal', doc='')
    alarm = Cpt(EpicsSignalWithRBV, ':ALARM', kind='normal', doc='')
    backing_pressure_sp = Cpt(EpicsSignalWithRBV, ':BackingPressureSP',
        kind='omitted', doc='')
    inlet_pressure_sp = Cpt(EpicsSignalWithRBV, ':InletPressureSP',
        kind='omitted', doc='')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
        doc='interlock  is ok when true')


class PROPLC(Device):
    """
    Class for PLC-controlled Roughing Pump

    """
    switch_pump_on = Cpt(EpicsSignalWithRBV, ':RUN_SW', kind='omitted',
        doc='')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
        doc='interlock is ok when true')
    run_do = Cpt(EpicsSignalRO, ':RUN_DO_RBV', kind='normal', doc='')
    error = Cpt(EpicsSignalRO, ':ERROR_RBV', kind='normal', doc='')
    warn = Cpt(EpicsSignalRO, ':WARN_RBV', kind='normal', doc='')
    pump_at_speed = Cpt(EpicsSignalRO, ':AT_SPD_RBV', kind='normal', doc='')


class AgilentSerial(Device):
    """
    Class for Agilent Turbo Pump controlled via serial

    """
    run = Cpt(EpicsSignal, ':RUN', kind='omitted', doc='')
    config = Cpt(EpicsSignal, ':CONFIG', kind='omitted', doc='')
    softstart = Cpt(EpicsSignal, ':SOFTSTART', kind='omitted', doc='')
    sp_type = Cpt(EpicsSignal, ':SP_TYPE', kind='omitted', doc='')
    sp_calcdis = Cpt(EpicsSignal, ':SP_CALCDIS', kind='omitted', doc='')
    sp_dis = Cpt(EpicsSignal, ':SP_DIS', kind='omitted', doc='')
    sp_writeval = Cpt(EpicsSignal, ':SP_WRITEVAL', kind='omitted', doc='')
    sp_freq = Cpt(EpicsSignal, ':SP_FREQ', kind='omitted', doc='')
    sp_current = Cpt(EpicsSignal, ':SP_CURRENT', kind='omitted', doc='')
    sp_time = Cpt(EpicsSignal, ':SP_TIME', kind='omitted', doc='')
    sp_delay = Cpt(EpicsSignal, ':SP_DELAY', kind='omitted', doc='')
    sp_polarity = Cpt(EpicsSignal, ':SP_POLARITY', kind='omitted', doc='')
    sp_hys = Cpt(EpicsSignal, ':SP_HYS', kind='omitted', doc='')
    water_cooling = Cpt(EpicsSignal, ':WATER_COOLING', kind='normal', doc='')
    active_stop = Cpt(EpicsSignal, ':ACTIVE_STOP', kind='normal', doc='')
    interlock_type = Cpt(EpicsSignal, ':INTERLOCK_TYPE', kind='omitted', doc='')
    ao_type = Cpt(EpicsSignal, ':AO_TYPE', kind='omitted', doc='')
    rot_freq = Cpt(EpicsSignal, ':ROT_FREQ', kind='normal', doc='')
    vent_valve = Cpt(EpicsSignal, ':VENT_VALVE', kind='omitted', doc='')
    vent_valve_operation = Cpt(EpicsSignal, ':VENT_VALVE_OPERATION',
        kind='omitted', doc='')
    vent_valve_delay = Cpt(EpicsSignal, ':VENT_VALVE_DELAY', kind='omitted',
        doc='')
    vent_valve_raw = Cpt(EpicsSignal, ':VENT_VALVE_RAW', kind='omitted',
        doc='')
    pump_current = Cpt(EpicsSignalRO, ':PUMP_CURRENT', kind='omitted',
        doc='')
    pump_voltage = Cpt(EpicsSignalRO, ':PUMP_VOLTAGE', kind='normal',
        doc='')
    pump_power = Cpt(EpicsSignalRO, ':PUMP_POWER', kind='normal', doc='')
    pump_drive_freq = Cpt(EpicsSignalRO, ':PUMP_DRIVE_FREQ', kind='normal',
        doc='')
    pump_temp = Cpt(EpicsSignalRO, ':PUMP_TEMP', kind='normal', doc='')
    pump_status = Cpt(EpicsSignalRO, ':PUMP_STATUS', kind='normal', doc='')
    pump_error = Cpt(EpicsSignalRO, ':PUMP_ERROR', kind='normal', doc='')


class Navigator(AgilentSerial):
    """
    Class for Navigator Pump controlled via serial

    """
    low_speed = Cpt(EpicsSignalRO, ':LOW_SPEED', kind='omitted', doc='')
    low_speed_freq = Cpt(EpicsSignalRO, ':LOW_SPEED_FREQ', kind='omitted',
        doc='')
    sp_power = Cpt(EpicsSignalRO, ':SP_POWER', kind='omitted', doc='')
    sp_time = Cpt(EpicsSignalRO, ':SP_TIME', kind='omitted', doc='')
    sp_normal = Cpt(EpicsSignalRO, ':SP_NORMAL', kind='omitted', doc='')
    sp_pressure = Cpt(EpicsSignalRO, ':SP_PRESSURE', kind='omitted', doc='')
    vent_open_time = Cpt(EpicsSignalRO, ':VENT_OPEN_TIME', kind='omitted',
        doc='')
    vent_open_time_raw = Cpt(EpicsSignalRO, ':VENT_OPEN_TIME_RAW',
        kind='omitted', doc='')
    power_limit = Cpt(EpicsSignalRO, ':POWER_LIMIT', kind='omitted', doc='')
    gas_load_type = Cpt(EpicsSignalRO, ':GAS_LOAD_TYPE', kind='omitted',
        doc='')
    press_read_corr = Cpt(EpicsSignalRO, ':PRESS_READ_CORR', kind='omitted',
        doc='')
    sp_press_unit = Cpt(EpicsSignalRO, ':SP_PRESS_UNIT', kind='omitted',
        doc='')
    sp_write_press_unit = Cpt(EpicsSignalRO, ':SP_WRITE_PRESS_UNIT',
        kind='omitted', doc='')
    stop_speed_reading = Cpt(EpicsSignalRO, ':STOP_SPEED_READING',
        kind='omitted', doc='')
    ctrl_heatsink_temp = Cpt(EpicsSignalRO, ':CTRL_HEATSINK_TEMP',
        kind='omitted', doc='')
    ctrl_air_temp = Cpt(EpicsSignalRO, ':CTRL_AIR_TEMP', kind='omitted',
        doc='')


class GammaPCT(Device):
    """
    Class for Gamma Pump Controller accessed via serial

    """
    model = Cpt(EpicsSignalRO, ':MODEL', kind='normal', doc='')
    fwversion = Cpt(EpicsSignalRO, ':FWVERSION', kind='normal', doc='')
    ashvedes = Cpt(EpicsSignal, ':ASHVEDES', kind='omitted', doc='')
    ashve = Cpt(EpicsSignalRO, ':ASHVE', kind='normal', doc='')
    aspowerdes = Cpt(EpicsSignal, ':ASPOWERDES', kind='omitted', doc='')
    aspower = Cpt(EpicsSignalRO, ':ASPOWER', kind='normal', doc='')
    pegudes = Cpt(EpicsSignal, ':PEGUDES', kind='omitted', doc='')
    masterreset = Cpt(EpicsSignal, ':MASTERRESET', kind='omitted', doc='')


class QPCPCT(GammaPCT):
    """
    Class for Quad Pump Controller accessed via serial

    """
    do_reset = Cpt(EpicsSignal, ':DO_RESET', kind='omitted', doc='')


class PIPSerial(Device):
    """
    Class for Positive Ion Pump controlled via serial

    """
    imon = Cpt(EpicsSignalRO, ':IMON', kind='hinted', doc='')
    pmon = Cpt(EpicsSignalRO, ':PMON', kind='hinted', doc='')
    pmonlog = Cpt(EpicsSignalRO, ':PMONLOG', kind='normal', doc='')
    vmon = Cpt(EpicsSignalRO, ':VMON', kind='normal', doc='')
    statusraw = Cpt(EpicsSignalRO, ':STATUSRAW', kind='omitted', doc='')
    statuscalc = Cpt(EpicsSignalRO, ':STATUSCALC', kind='omitted', doc='')
    status = Cpt(EpicsSignalRO, ':STATUS', kind='normal', doc='')
    statuscodecl = Cpt(EpicsSignalRO, ':STATUSCODECL', kind='omitted', doc='')
    statuscode = Cpt(EpicsSignalRO, ':STATUSCODE', kind='omitted', doc='')
    pumpsizedes = Cpt(EpicsSignal, ':PUMPSIZEDES', kind='omitted', doc='')
    pumpsize = Cpt(EpicsSignal, ':PUMPSIZE', kind='omitted', doc='')
    calfactordes = Cpt(EpicsSignal, ':CALFACTORDES', kind='omitted', doc='')
    calfactor = Cpt(EpicsSignal, ':CALFACTOR', kind='omitted', doc='')
    aomodedes = Cpt(EpicsSignal, ':AOMODEDES', kind='omitted', doc='')
    aomode = Cpt(EpicsSignal, ':AOMODE', kind='omitted', doc='')
    statedes = Cpt(EpicsSignal, ':STATEDES', kind='omitted', doc='')
    statemon = Cpt(EpicsSignalRO, ':STATEMON', kind='normal', doc='')
    dispdes = Cpt(EpicsSignal, ':DISPDES', kind='omitted', doc='')
    pname = Cpt(EpicsSignalRO, ':PNAME', kind='normal', doc='')
    pnamedes = Cpt(EpicsSignal, ':PNAMEDES', kind='omitted', doc='')
    vpcname = Cpt(EpicsSignal, ':VPCNAME', kind='omitted', doc='')


# factory function for IonPumps
def IonPump(prefix, *, name, **kwargs):
    """
    Ion Pump

    Parameters
    ----------
    prefix : ``str``
        Ion Pump PV

    name : ``str``
        Alias for the ion pump

    (optional) prefix_controller : ``str``
        Ion Pump Controller base PV
    """

    if 'prefix_controller' not in kwargs:
        return IonPumpBase(prefix, name=name, **kwargs)

    return IonPumpWithController(prefix, name=name, **kwargs)
