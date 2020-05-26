"""
Classes for cards attached to EK9000 bus couplers.
"""

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO


class EL3174_AI_Ch(Device):
    """
    EL3174 analog input card channel.

    Can be used to digitize a variety of sensors.

    Parameters
    ----------
    prefix : str
        The PV base of the card.
    """
    _Measured = Cpt(EpicsSignalRO, '.VAL', name='Converted Signal',
                    kind='normal')
    _Raw_ADC = Cpt(EpicsSignalRO, '.RVAL', name='Raw Signal', kind='config')
    _EGU = Cpt(EpicsSignal, '.EGU', name='Signal Units', kind='config')
    _EGU_Max = Cpt(EpicsSignal, '.EGUF', name='EGU Max', kind='config')
    _EGU_Min = Cpt(EpicsSignal, '.EGUL', name='EGU Min', kind='config')
    _Conversion = Cpt(EpicsSignal, '.LINR', name='Conv. Method', kind='config')
    _Precision = Cpt(EpicsSignal, '.PREC', name='Precision', kind='config')


class EnvironmentalMonitor(Device):
    """
    Class for the MODS environmental monitoring system, which typically
    consists of three measurements: P, T, and %RH.
    """

    _Pressure = Cpt(EL3174_AI_Ch, ':1', name='Pressure')
    _Humidity = Cpt(EL3174_AI_Ch, ':2', name='Relative Humidity')
    _Temperature = Cpt(EL3174_AI_Ch, ':3', name='Temperature')
