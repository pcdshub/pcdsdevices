"""
Sensor classes.

Classes for the various thermocouples, rtds, flow meters, O2 sensors, etc.
"""
from ophyd import Component as Cpt
from ophyd import Device

from .interface import BaseInterface
from .signal import NotImplementedSignal, PytmcSignal


class TwinCATThermocouple(BaseInterface, Device):
    """
    Basic twincat temperature sensor class.

    Assumes we're using the ``FB_ThermoCouple`` function block from
    ``lcls-twincat-general``.
    """

    temperature = Cpt(PytmcSignal, ':STC:TEMP', io='i', kind='normal')
    sensor_connected = Cpt(PytmcSignal, ':STC:CONN', io='i', kind='normal')
    error = Cpt(PytmcSignal, ':STC:ERR', io='i', kind='normal')


class TwinCATTempSensor(BaseInterface, Device):
    """
    Basic twincat temperature sensor class.

    Assumes we're using the ``FB_TempSensor`` function block from
    ``lcls-twincat-general``.
    """

    temperature = Cpt(PytmcSignal, ':TEMP', io='i', kind='normal')
    sensor_connected = Cpt(PytmcSignal, ':CONN', io='i', kind='normal')
    error = Cpt(PytmcSignal, ':ERR', io='i', kind='normal')


class RTD(BaseInterface, Device):
    """
    Resistive Temperature Device.

    Can be thermistors, or pt100 (or similar).

    Parameters
    ----------
    prefix : str
        The PV base of the device.
    """

    not_implemented = Cpt(NotImplementedSignal, kind='normal')
