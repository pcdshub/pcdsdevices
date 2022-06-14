import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

logger = logging.getLogger(__name__)


class RohdSchwarzPowerSupply(Device):
    """
    Class to define PVs of all channels of the RSPowerSupply NGP800.

        The base PV of the relevant RSPowersupply.

    channel 1
    """

    ch1_current = Cpt(EpicsSignal, ':1:CURR', kind='normal')
    ch1_current_step = Cpt(EpicsSignal, ':1:CURR_STEP', kind='normal')
    ch1_current_twk = Cpt(EpicsSignal, ':1:CURR_TWK', kind='normal')
    ch1_select = Cpt(EpicsSignal, ':1:SELECT', kind='normal')
    ch1_set_current = Cpt(EpicsSignal, ':1:SET_CURR', kind='normal')
    ch1_set_voltage = Cpt(EpicsSignal, ':1:SET_VOLT', kind='normal')
    ch1_voltage = Cpt(EpicsSignal, ':1:VOLT', kind='normal')
    ch1_voltage_step = Cpt(EpicsSignal, ':1:VOLT_STEP', kind='normal')
    ch1_voltage_twk = Cpt(EpicsSignal, ':1:VOLT_TWK', kind='normal')
    ch1_curr_step_rbv = Cpt(EpicsSignalRO, ':1:CURR_STEP_RBV', kind='hinted')
    ch1_volt_step_rbv = Cpt(EpicsSignalRO, ':1:VOLT_STEP_RBV', kind='hinted')
    ch1_set_current_rbv = Cpt(EpicsSignalRO, ':1:SET_CURR_RBV', kind='hinted')
    ch1_set_voltage_rbv = Cpt(EpicsSignalRO, ':1:SET_VOLT_RBV', kind='hinted')
    ch1_status = Cpt(EpicsSignalRO, ':1:STATUS', kind='hinted')
    """
    channel 2
    """
    ch2_current = Cpt(EpicsSignal, ':2:CURR', kind='normal')
    ch2_current_step = Cpt(EpicsSignal, ':2:CURR_STEP', kind='normal')
    ch2_current_twk = Cpt(EpicsSignal, ':2:CURR_TWK', kind='normal')
    ch2_select = Cpt(EpicsSignal, ':2:SELECT', kind='normal')
    ch2_set_current = Cpt(EpicsSignal, ':2:SET_CURR', kind='normal')
    ch2_set_voltage = Cpt(EpicsSignal, ':2:SET_VOLT', kind='normal')
    ch2_voltage = Cpt(EpicsSignal, ':2:VOLT', kind='normal')
    ch2_voltage_step = Cpt(EpicsSignal, ':2:VOLT_STEP', kind='normal')
    ch2_voltage_twk = Cpt(EpicsSignal, ':2:VOLT_TWK', kind='normal')
    ch2_curr_step_rbv = Cpt(EpicsSignalRO, ':2:CURR_STEP_RBV', kind='hinted')
    ch2_volt_step_rbv = Cpt(EpicsSignalRO, ':2:VOLT_STEP_RBV', kind='hinted')
    ch2_set_current_rbv = Cpt(EpicsSignalRO, ':2:SET_CURR_RBV', kind='hinted')
    ch2_set_voltage_rbv = Cpt(EpicsSignalRO, ':2:SET_VOLT_RBV', kind='hinted')
    ch2_status = Cpt(EpicsSignalRO, ':2:STATUS', kind='hinted')
    """
    channel3
    """
    ch3_current = Cpt(EpicsSignal, ':3:CURR', kind='normal')
    ch3_current_step = Cpt(EpicsSignal, ':3:CURR_STEP', kind='normal')
    ch3_current_twk = Cpt(EpicsSignal, ':3:CURR_TWK', kind='normal')
    ch3_select = Cpt(EpicsSignal, ':3:SELECT', kind='normal')
    ch3_set_current = Cpt(EpicsSignal, ':3:SET_CURR', kind='normal')
    ch3_set_voltage = Cpt(EpicsSignal, ':3:SET_VOLT', kind='normal')
    ch3_voltage = Cpt(EpicsSignal, ':3:VOLT', kind='normal')
    ch3_voltage_step = Cpt(EpicsSignal, ':3:VOLT_STEP', kind='normal')
    ch3_voltage_twk = Cpt(EpicsSignal, ':3:VOLT_TWK', kind='normal')
    ch3_curr_step_rbv = Cpt(EpicsSignalRO, ':3:CURR_STEP_RBV', kind='hinted')
    ch3_volt_step_rbv = Cpt(EpicsSignalRO, ':3:VOLT_STEP_RBV', kind='hinted')
    ch3_set_current_rbv = Cpt(EpicsSignalRO, ':3:SET_CURR_RBV', kind='hinted')
    ch3_set_voltage_rbv = Cpt(EpicsSignalRO, ':3:SET_VOLT_RBV', kind='hinted')
    ch3_status = Cpt(EpicsSignalRO, ':3:STATUS', kind='hinted')
    """
    channel 4
    """
    ch4_current = Cpt(EpicsSignal, ':4:CURR', kind='normal')
    ch4_current_step = Cpt(EpicsSignal, ':4:CURR_STEP', kind='normal')
    ch4_current_twk = Cpt(EpicsSignal, ':4:CURR_TWK', kind='normal')
    ch4_select = Cpt(EpicsSignal, ':4:SELECT', kind='normal')
    ch4_set_current = Cpt(EpicsSignal, ':4:SET_CURR', kind='normal')
    ch4_set_voltage = Cpt(EpicsSignal, ':4:SET_VOLT', kind='normal')
    ch4_voltage = Cpt(EpicsSignal, ':4:VOLT', kind='normal')
    ch4_voltage_step = Cpt(EpicsSignal, ':4:VOLT_STEP', kind='normal')
    ch4_voltage_twk = Cpt(EpicsSignal, ':4:VOLT_TWK', kind='normal')
    ch4_curr_step_rbv = Cpt(EpicsSignalRO, ':4:CURR_STEP_RBV', kind='hinted')
    ch4_volt_step_rbv = Cpt(EpicsSignalRO, ':4:VOLT_STEP_RBV', kind='hinted')
    ch4_set_current_rbv = Cpt(EpicsSignalRO, ':4:SET_CURR_RBV', kind='hinted')
    ch4_set_voltage_rbv = Cpt(EpicsSignalRO, ':4:SET_VOLT_RBV', kind='hinted')
    ch4_status = Cpt(EpicsSignalRO, ':4:STATUS', kind='hinted')
