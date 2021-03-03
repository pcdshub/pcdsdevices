"""
Standard classes for LCLS Pumps.
"""
import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd import FormattedComponent as FCpt

from .doc_stubs import IonPump_base
from .interface import BaseInterface

logger = logging.getLogger(__name__)


class TurboPump(BaseInterface, Device):
    """Turbo Vacuum Pump."""
    atspeed = Cpt(EpicsSignal, ':ATSPEED_DI', kind='normal')
    start = Cpt(EpicsSignal, ':START_SW', kind='normal')

    tab_whitelist = ['run', 'stop', 'atspeed']

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)


class EbaraPump(BaseInterface, Device):
    """Ebara Turbo Pump."""
    start = Cpt(EpicsSignal, ':MPSTART_SW', kind='normal')

    tab_whitelist = ['run', 'stop']

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)


class GammaController(BaseInterface, Device):
    """Ion Pump Gamma controller."""
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


class IonPumpBase(BaseInterface, Device):
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

    prefix_controller : str
        Ion Pump Controller base PV.
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
    Class for PLC-controlled Ion Pumps.

    Newer class. This and below are still missing some functionality.
    Still need to work out replacement of old classes.
    """

    pressure = Cpt(EpicsSignalRO, ':PRESS_RBV', kind='hinted',
                   doc='pressure reading')
    high_voltage_do = Cpt(EpicsSignalRO, ':HV_DO_RBV', kind='normal',
                          doc='high voltage digital output')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
                       doc='interlock  is ok when true')
    protection_setpoint = Cpt(EpicsSignalWithRBV, ':AT_VAC_SP', kind='config',
                              doc='Protection/At Vacuum Setpoint')
    setpoint_hysteresis = Cpt(EpicsSignalWithRBV, ':SP_HYS', kind='config',
                              doc='Protection Setpoint Hysteresis')
    pump_on_status = Cpt(EpicsSignalRO, ':HV_DI_RBV', kind='normal',
                         doc='ion pump output state')
    pump_state = Cpt(EpicsSignalRO, ':STATE_RBV', kind='hinted')
    at_vac_setpoint = Cpt(EpicsSignalWithRBV, ':AT_VAC_SP', kind='omitted',
                          doc='at vacuum set point')
    high_voltage_switch = Cpt(EpicsSignalWithRBV, ':HV_SW', kind='config',
                              doc='epics command to switch on the '
                              'high voltage')
    plc_ai_offset = Cpt(EpicsSignalRO, ':AI_Offset_RBV', kind='config',
                        doc=('Analog input offset must match ion pump '
                             'analog ouput offset. Default: 13'))
    auto_on = Cpt(EpicsSignalRO, ':Auto_On_RBV', kind='config',
                  doc=('Setting to automatically turn on the ion pump when the'
                       'reference gauge pressure is below protection '
                       'setpoint'))
    override_status = Cpt(EpicsSignalRO, ':OVRD_ON', kind='omitted',
                          doc='Regional Override Status')
    override_force_on = Cpt(EpicsSignalWithRBV, ':FORCE_START', kind='omitted',
                            doc='Force Ion Pump to turn on')
    qpc_name = Cpt(EpicsSignalRO, ':VPCNAME', kind='config',
                   doc='Quad Ion Pump Controller Name')
    qpc_pumpsize = Cpt(EpicsSignalRO, ':PUMPSIZE', kind='config',
                       doc='Ion Pump Size (L/s)')
    interlock_device = Cpt(EpicsSignalRO, ':ILK_DEVICE_RBV', kind='config',
                           string=True,
                           doc='Vacuum device used for interlocking this pump')


class PTMPLC(Device):
    """Class for PLC-controlled Turbo Pump."""
    switch_pump_on = Cpt(EpicsSignalWithRBV, ':RUN_SW', kind='normal')
    reset_fault = Cpt(EpicsSignalWithRBV, ':RST_SW', kind='normal')
    run_do = Cpt(EpicsSignalRO, ':RUN_DO_RBV', kind='normal')
    pump_at_speed = Cpt(EpicsSignalRO, ':AT_SPD_RBV', kind='normal')
    pump_accelerating = Cpt(EpicsSignalRO, ':ACCEL_RBV', kind='normal')
    pump_speed = Cpt(EpicsSignalRO, ':SPEED_RBV', kind='normal')
    fault = Cpt(EpicsSignalRO, ':FAULT_RBV', kind='normal')
    warn = Cpt(EpicsSignalRO, ':WARN_RBV', kind='normal')
    alarm = Cpt(EpicsSignalRO, ':ALARM_RBV', kind='normal')
    backingpressure_sp = Cpt(EpicsSignalWithRBV, ':BP_SP', kind='config')
    inletpressure_sp = Cpt(EpicsSignalWithRBV, ':IP_SP', kind='config')
    interlock_status = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
                           doc='interlock  is ok when true')


class PROPLC(Device):
    """Class for PLC-controlled Roughing Pump."""
    switch_pump_on = Cpt(EpicsSignalWithRBV, ':RUN_SW', kind='omitted')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
                       doc='interlock is ok when true')
    run_do = Cpt(EpicsSignalRO, ':RUN_DO_RBV', kind='normal')
    error = Cpt(EpicsSignalRO, ':ERROR_RBV', kind='normal')
    warn = Cpt(EpicsSignalRO, ':WARN_RBV', kind='normal')
    pump_at_speed = Cpt(EpicsSignalRO, ':AT_SPD_RBV', kind='normal')


class Ebara_EV_A03_1(PROPLC):
    """Class for the Ebara EV-A03-1 model of roughing pump."""
    remote = Cpt(EpicsSignalWithRBV, ':REMOTE', kind='omitted')
    alarm = Cpt(EpicsSignalRO, ':ALARM_OK_RBV', kind='normal')
    run_di = Cpt(EpicsSignalRO, ':RUN_DI_RBV', kind='omitted')


class AgilentSerial(Device):
    """Class for Agilent Turbo Pump controlled via serial."""
    run = Cpt(EpicsSignal, ':RUN', kind='omitted')
    config = Cpt(EpicsSignal, ':CONFIG', kind='omitted')
    softstart = Cpt(EpicsSignal, ':SOFTSTART', kind='omitted')
    sp_type = Cpt(EpicsSignal, ':SP_TYPE', kind='omitted')
    sp_calcdis = Cpt(EpicsSignal, ':SP_CALCDIS', kind='omitted')
    sp_dis = Cpt(EpicsSignal, ':SP_DIS', kind='omitted')
    sp_writeval = Cpt(EpicsSignal, ':SP_WRITEVAL', kind='omitted')
    sp_freq = Cpt(EpicsSignal, ':SP_FREQ', kind='omitted')
    sp_current = Cpt(EpicsSignal, ':SP_CURRENT', kind='omitted')
    sp_time = Cpt(EpicsSignal, ':SP_TIME', kind='omitted')
    sp_delay = Cpt(EpicsSignal, ':SP_DELAY', kind='omitted')
    sp_polarity = Cpt(EpicsSignal, ':SP_POLARITY', kind='omitted')
    sp_hys = Cpt(EpicsSignal, ':SP_HYS', kind='omitted')
    water_cooling = Cpt(EpicsSignal, ':WATER_COOLING', kind='normal')
    active_stop = Cpt(EpicsSignal, ':ACTIVE_STOP', kind='normal')
    interlock_type = Cpt(EpicsSignal, ':INTERLOCK_TYPE', kind='omitted')
    ao_type = Cpt(EpicsSignal, ':AO_TYPE', kind='omitted')
    rot_freq = Cpt(EpicsSignal, ':ROT_FREQ', kind='normal')
    vent_valve = Cpt(EpicsSignal, ':VENT_VALVE', kind='omitted')
    vent_valve_operation = Cpt(EpicsSignal, ':VENT_VALVE_OPERATION',
                               kind='omitted')
    vent_valve_delay = Cpt(EpicsSignal, ':VENT_VALVE_DELAY', kind='omitted')
    vent_valve_raw = Cpt(EpicsSignal, ':VENT_VALVE_RAW', kind='omitted')
    pump_current = Cpt(EpicsSignalRO, ':PUMP_CURRENT_RBV', kind='omitted')
    pump_voltage = Cpt(EpicsSignalRO, ':PUMP_VOLTAGE_RBV', kind='normal')
    pump_power = Cpt(EpicsSignalRO, ':PUMP_POWER_RBV', kind='normal')
    pump_drive_freq = Cpt(EpicsSignalRO, ':PUMP_DRIVE_FREQ_RBV', kind='normal')
    pump_temp = Cpt(EpicsSignalRO, ':PUMP_TEMP_RBV', kind='normal')
    pump_status = Cpt(EpicsSignalRO, ':PUMP_STATUS_RBV', kind='normal')
    pump_error = Cpt(EpicsSignalRO, ':PUMP_ERROR_RBV', kind='normal')


class Navigator(AgilentSerial):
    """Class for Navigator Pump controlled via serial."""
    low_speed = Cpt(EpicsSignalRO, ':LOW_SPEED_RBV', kind='omitted')
    low_speed_freq = Cpt(EpicsSignalRO, ':LOW_SPEED_FREQ_RBV', kind='omitted')
    sp_power = Cpt(EpicsSignalRO, ':SP_POWER_RBV', kind='omitted')
    sp_time = Cpt(EpicsSignalRO, ':SP_TIME_RBV', kind='omitted')
    sp_normal = Cpt(EpicsSignalRO, ':SP_NORMAL_RBV', kind='omitted')
    sp_pressure = Cpt(EpicsSignalRO, ':SP_PRESSURE_RBV', kind='omitted')
    vent_open_time = Cpt(EpicsSignalRO, ':VENT_OPEN_TIME_RBV', kind='omitted')
    vent_open_time_raw = Cpt(EpicsSignalRO, ':VENT_OPEN_TIME_RAW_RBV',
                             kind='omitted')
    power_limit = Cpt(EpicsSignalRO, ':POWER_LIMIT_RBV', kind='omitted')
    gas_load_type = Cpt(EpicsSignalRO, ':GAS_LOAD_TYPE_RBV', kind='omitted')
    press_read_corr = Cpt(EpicsSignalRO, ':PRESS_READ_CORR_RBV',
                          kind='omitted')
    sp_press_unit = Cpt(EpicsSignalRO, ':SP_PRESS_UNIT_RBV', kind='omitted')
    sp_write_press_unit = Cpt(EpicsSignalRO, ':SP_WRITE_PRESS_UNIT_RBV',
                              kind='omitted')
    stop_speed_reading = Cpt(EpicsSignalRO, ':STOP_SPEED_READING_RBV',
                             kind='omitted')
    ctrl_heatsink_temp = Cpt(EpicsSignalRO, ':CTRL_HEATSINK_TEMP_RBV',
                             kind='omitted')
    ctrl_air_temp = Cpt(EpicsSignalRO, ':CTRL_AIR_TEMP_RBV', kind='omitted')


class GammaPCT(Device):
    """Class for Gamma Pump Controller accessed via serial."""
    model = Cpt(EpicsSignalRO, ':MODEL_RBV', kind='normal')
    fwversion = Cpt(EpicsSignalRO, ':FWVERSION_RBV', kind='normal')
    ashvedes = Cpt(EpicsSignal, ':ASHVEDES', kind='omitted')
    ashve = Cpt(EpicsSignalRO, ':ASHVE_RBV', kind='normal')
    aspowerdes = Cpt(EpicsSignal, ':ASPOWERDES', kind='omitted')
    aspower = Cpt(EpicsSignalRO, ':ASPOWER_RBV', kind='normal')
    pegudes = Cpt(EpicsSignal, ':PEGUDES', kind='omitted')
    masterreset = Cpt(EpicsSignal, ':MASTERRESET', kind='omitted')


class QPCPCT(GammaPCT):
    """Class for Quad Pump Controller accessed via ethernet."""
    do_reset = Cpt(EpicsSignal, ':DO_RESET', kind='omitted')


class PIPSerial(Device):
    """Class for Positive Ion Pump controlled via serial."""
    imon = Cpt(EpicsSignalRO, ':IMON_RBV', kind='hinted')
    pmon = Cpt(EpicsSignalRO, ':PMON_RBV', kind='hinted')
    pmonlog = Cpt(EpicsSignalRO, ':PMONLOG_RBV', kind='normal')
    vmon = Cpt(EpicsSignalRO, ':VMON_RBV', kind='normal')
    statusraw = Cpt(EpicsSignalRO, ':STATUSRAW_RBV', kind='omitted')
    statuscalc = Cpt(EpicsSignalRO, ':STATUSCALC_RBV', kind='omitted')
    status = Cpt(EpicsSignalRO, ':STATUS_RBV', kind='normal')
    statuscodecl = Cpt(EpicsSignalRO, ':STATUSCODECL_RBV', kind='omitted')
    statuscode = Cpt(EpicsSignalRO, ':STATUSCODE_RBV', kind='omitted')
    pumpsizedes = Cpt(EpicsSignal, ':PUMPSIZEDES', kind='omitted')
    pumpsize = Cpt(EpicsSignal, ':PUMPSIZE', kind='omitted')
    calfactordes = Cpt(EpicsSignal, ':CALFACTORDES', kind='omitted')
    calfactor = Cpt(EpicsSignal, ':CALFACTOR', kind='omitted')
    aomodedes = Cpt(EpicsSignal, ':AOMODEDES', kind='omitted')
    aomode = Cpt(EpicsSignal, ':AOMODE', kind='omitted')
    statedes = Cpt(EpicsSignal, ':STATEDES', kind='omitted')
    statemon = Cpt(EpicsSignalRO, ':STATEMON_RBV', kind='normal')
    dispdes = Cpt(EpicsSignal, ':DISPDES', kind='omitted')
    pname = Cpt(EpicsSignalRO, ':PNAME_RBV', kind='normal')
    pnamedes = Cpt(EpicsSignal, ':PNAMEDES', kind='omitted')
    vpcname = Cpt(EpicsSignal, ':VPCNAME', kind='omitted')


# factory function for IonPumps
def IonPump(prefix, *, name, **kwargs):
    """
    Ion Pump

    Parameters
    ----------
    prefix : str
        Base PV for the Ion Pump.

    name : str
        Alias for the Ion Pump.

    prefix_controller : str, optional
        Ion Pump Controller base PV.
    """

    if 'prefix_controller' not in kwargs:
        return IonPumpBase(prefix, name=name, **kwargs)

    return IonPumpWithController(prefix, name=name, **kwargs)
