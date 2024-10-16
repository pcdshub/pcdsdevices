"""
Classes for lakeshore temperature controller
"""
import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class Heater(BaseInterface, Device):
    """
    HeaterState Channel Object.

    Parameters
    ----------
    prefix : str
        The EPICS base of the HeaterState PV. E.g.:'XCS:USR:TCT:02:'
    channel : str
        The channel number of the Heater State.
    """
    htr_state = FCpt(EpicsSignal, '{prefix}:GET_RANGE_{channel}', write_pv='{prefix}:PUT_RANGE_{channel}', kind='normal', doc='heater range')
    htr_state_rbv = FCpt(EpicsSignalRO, '{prefix}:GET_HTRSTAT_{channel}', kind='normal')

    tab_component_names = True

    def __init__(self, prefix, channel, **kwargs):
        self.channel = channel
        super().__init__(prefix, **kwargs)


class TemperatureSensor(BaseInterface, Device):
    """
    Temperature Sensor Channel Object.

    Parameters
    ----------
    prefix : str
        The channel number or letter of the Temperature Sesnor.
    channel : str
        The channel number of the Heater State.
    """
    input_name = FCpt(EpicsSignalRO, '{prefix}:GET_INNAME_{channel}', kind='config')
    temp = FCpt(EpicsSignalRO, '{prefix}:GET_TEMP_{channel}', kind='normal')
    units = FCpt(EpicsSignal, '{prefix}:GET_UNITS_{channel}', write_pv=':PUT_UNITS_{channel}', kind='normal')
    sensor_type = FCpt(EpicsSignalRO, '{prefix}:GET_SENSOR_{channel}', kind='normal')

    tab_component_names = True

    def __init__(self, prefix, channel, **kwargs):
        self.channel = channel
        super().__init__(prefix, **kwargs)


class Lakeshore336(BaseInterface, Device):
    """
    This class supports the Lakeshore Model 336 Temperature controller.

    It includes:
    2 loops for setting the temperature
    2 range controls for the heater
    2 sets of controls for manual and analog output
    4 temperature sensors
    Various read-only signals.
    """

    # temp loops
    set_temp_loop_1 = Cpt(EpicsSignal, ':GET_SOLL_1', write_pv=':PUT_SOLL_1', kind='normal')
    set_temp_loop_2 = Cpt(EpicsSignal, ':GET_SOLL_2', write_pv=':PUT_SOLL_2', kind='normal')

    # manual output loops
    man_loop_1 = Cpt(EpicsSignal, ':GET_MOUT_1', write_pv=':PUT_MOUT_1', kind='normal')
    man_loop_2 = Cpt(EpicsSignal, ':GET_MOUT_2', write_pv=':PUT_MOUT_2', kind='normal')

    # analog output loops
    an_loop_3 = Cpt(EpicsSignal, ':GET_AOUT_3', write_pv=':PUT_MOUT_3', kind='normal')
    an_loop_4 = Cpt(EpicsSignal, ':GET_AOUT_4', write_pv=':PUT_MOUT_4', kind='normal')

    # heater control
    set_heater_1 = Cpt(Heater, '', channel='1', kind="normal")
    set_heater_2 = Cpt(Heater, '', channel='2', kind="normal")

    # 4 temperature sensors
    temp_A = Cpt(TemperatureSensor, '', channel='A', kind='normal')
    temp_B = Cpt(TemperatureSensor, '', channel='B', kind='normal')
    temp_C = Cpt(TemperatureSensor, '', channel='C', kind='normal')
    temp_D = Cpt(TemperatureSensor, '', channel='D', kind='normal')

    # device control mode
    mode = Cpt(EpicsSignal, 'GET_MODE', write_pv='PUT_MODE', kind='normal', doc='control mode')

    # read only
    loop_ramp_1 = Cpt(EpicsSignalRO, ':GET_RAMP_1', kind='normal')
    loop_ramp_2 = Cpt(EpicsSignalRO, ':GET_RAMP_2', kind='normal')
    htr_out_1 = Cpt(EpicsSignalRO, ':GET_HTR_1', kind='normal')
    htr_out_2 = Cpt(EpicsSignalRO, ':GET_HTR_2', kind='normal')

    tab_component_names = True
