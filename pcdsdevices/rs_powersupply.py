import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

logger = logging.getLogger(__name__)


class RSchannel(Device):
    """
    Class to define PVs of all channels of the RSPowerSupply NGP800.
    prefix: str
        The base PV of the relevant RohdeSchwarzPowersupply.
    name: str, keyword-only
        A name to refer to the relevant RohdeSchwarzPowersupply
    """

    current = Cpt(EpicsSignal, 'CURR', kind='normal', doc='Current in Amps')
    current_step = Cpt(EpicsSignal, 'CURR_STEP', kind='normal')
    current_twk = Cpt(EpicsSignal, 'CURR_TWK', kind='normal')
    select = Cpt(EpicsSignal, 'SELECT', kind='normal')
    set_current = Cpt(EpicsSignal, 'SET_CURR', kind='normal')
    set_voltage = Cpt(EpicsSignal, 'SET_VOLT', kind='normal')
    voltage = Cpt(EpicsSignal, 'VOLT', kind='normal', doc='Voltage in Volts')
    voltage_step = Cpt(EpicsSignal, 'VOLT_STEP', kind='normal')
    voltage_twk = Cpt(EpicsSignal, 'VOLT_TWK', kind='normal')
    curr_step_rbv = Cpt(EpicsSignalRO, 'CURR_STEP_RBV', kind='hinted')
    volt_step_rbv = Cpt(EpicsSignalRO, 'VOLT_STEP_RBV', kind='hinted')
    set_current_rbv = Cpt(EpicsSignalRO, 'SET_CURR_RBV', kind='hinted')
    set_voltage_rbv = Cpt(EpicsSignalRO, 'SET_VOLT_RBV', kind='hinted')
    status = Cpt(EpicsSignalRO, 'STATUS', kind='hinted')


class RohdeSchwarzPowerSupply(Device):
    """
    Class to define PVs of all channels of the RSPowerSupply NGP800.
    prefix: str
        The base PV of the relevant RohdeSchwarzPowersupply.
    name: str, keyword-only
        A name to refer to the relevant RohdeSchwarzPowersupply
    """

    ch1 = Cpt(RSchannel, ':1:', kind='normal')
    ch2 = Cpt(RSchannel, ':2:', kind='normal')
    ch3 = Cpt(RSchannel, ':3:', kind='normal')
    ch4 = Cpt(RSchannel, ':4:', kind='normal')
