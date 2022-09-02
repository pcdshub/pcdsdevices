import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

logger = logging.getLogger(__name__)


class RSChannel(Device):
    """
    Class to define PVs for a single channel of the RSPowerSupply NGP800.

    Parameters
    ----------
    prefix: str
        The base PV of the relevant Rohde-Schwarz channel.
    name: str, keyword-only
        A name to refer to the relevant Rohde-Schwarz channel.
    """

    current = Cpt(EpicsSignal, 'CURR', kind='normal',
                  doc='Current Setpoint in Amps')
    current_step = Cpt(EpicsSignal, 'CURR_STEP', write_pv='CURR_STEP',
                       kind='hinted', doc='Step size for Current in Amps')
    current_twk = Cpt(EpicsSignal, 'CURR_TWK', kind='normal')
    select = Cpt(EpicsSignal, 'SELECT', kind='normal')
    set_current = Cpt(EpicsSignal, 'SET_CURR', write_pv='SET_CURR',
                      kind='hinted', doc='Current Setpoint in Amps')
    set_voltage = Cpt(EpicsSignal, 'SET_VOLT', write_pv='SET_VOLT',
                      kind='hinted', doc='Voltage Setpoint in Volts')
    voltage = Cpt(EpicsSignal, 'VOLT', kind='normal',
                  doc='Actual Voltage in Volts')
    voltage_step = Cpt(EpicsSignal, 'VOLT_STEP', write_pv='VOLT_STEP',
                       kind='hinted', doc='Step size for Voltage in Volts')
    voltage_twk = Cpt(EpicsSignal, 'VOLT_TWK', kind='normal')
    curr_step_rbv = Cpt(EpicsSignalRO, 'CURR_STEP_RBV', kind='hinted')
    volt_step_rbv = Cpt(EpicsSignalRO, 'VOLT_STEP_RBV', kind='hinted')
    set_current_rbv = Cpt(EpicsSignalRO, 'SET_CURR_RBV', kind='hinted')
    set_voltage_rbv = Cpt(EpicsSignalRO, 'SET_VOLT_RBV', kind='hinted')
    status = Cpt(EpicsSignalRO, 'STATUS', kind='hinted')


class RohdeSchwarzPowerSupply(Device):
    """
    Class to define PVs of all channels of the RSPowerSupply NGP800.

    Parameters
    ----------
    prefix: str
        The base PV of the relevant RohdeSchwarzPowersupply.
    name: str, keyword-only
        A name to refer to the relevant RohdeSchwazPowersupply.
    """

    ch1 = Cpt(RSChannel, ':1:', kind='normal')
    ch2 = Cpt(RSChannel, ':2:', kind='normal')
    ch3 = Cpt(RSChannel, ':3:', kind='normal')
    ch4 = Cpt(RSChannel, ':4:', kind='normal')
