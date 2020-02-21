"""
Sensor classes

Classes for the various thermocouples, rtds, flow meters, O2 sensors, etc.
"""
from ophyd import Device, Component as Cpt

from .interface import BaseInterface
from .signal import PytmcSignal


class TwinCATThermoCouple(Device, BaseInterface):
    """
    Basic twincat temperature sensor class

    Assumes we're using the FB_ThermoCouple function block from
    lcls-twincat-general
    """
    temperature = Cpt(PytmcSignal, ':STC:TEMP', io='i', kind='normal')
    sensor_connected = Cpt(PytmcSignal, ':STC:CONN', io='i', kind='normal')
    error = Cpt(PytmcSignal, ':STC:ERR', io='i', kind='normal')
