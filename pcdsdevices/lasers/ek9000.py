"""
Classes for cards attached to EK9000 bus couplers.
"""

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO


class El3174AiCh(Device):
    """
    EL3174 analog input card channel.

    Can be used to digitize a variety of sensors.

    Parameters
    ----------
    prefix : str
        The PV base of the card.
    """
    Measured = Cpt(EpicsSignalRO, '.VAL', kind='normal')
    _Raw_ADC = Cpt(EpicsSignalRO, '.RVAL', kind='config')
    EGU = Cpt(EpicsSignal, '.EGU', kind='config')
    _EGU_Max = Cpt(EpicsSignal, '.EGUF', kind='config')
    _EGU_Min = Cpt(EpicsSignal, '.EGUL', kind='config')
    _Conversion = Cpt(EpicsSignal, '.LINR', kind='config')
    _Precision = Cpt(EpicsSignal, '.PREC', kind='config')


class EnvironmentalMonitor(Device):
    """
    Class for the MODS environmental monitoring system, which typically
    consists of three measurements: P, T, and %RH.
    """

    Pressure = Cpt(El3174AiCh, ':1')
    Humidity = Cpt(El3174AiCh, ':2')
    Temperature = Cpt(El3174AiCh, ':3')
