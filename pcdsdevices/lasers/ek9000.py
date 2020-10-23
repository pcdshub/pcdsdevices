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
    measured = Cpt(EpicsSignalRO, '.VAL', kind='normal')
    raw_adc = Cpt(EpicsSignalRO, '.RVAL', kind='config')
    egu = Cpt(EpicsSignal, '.EGU', kind='config')
    # TJ: These may be usefult late, but not now
    # egu_max = Cpt(EpicsSignal, '.EGUF', kind='config')
    # egu_min = Cpt(EpicsSignal, '.EGUL', kind='config')
    eslo = Cpt(EpicsSignal, '.ESLO', kind='config')
    eoff = Cpt(EpicsSignal, '.EOFF', kind='config')
    conversion = Cpt(EpicsSignal, '.LINR', kind='config')
    precision = Cpt(EpicsSignal, '.PREC', kind='config')


class EnvironmentalMonitor(Device):
    """
    Class for the MODS environmental monitoring system, which typically
    consists of three measurements: P, T, and %RH.
    """

    pressure = Cpt(El3174AiCh, ':1')
    humidity = Cpt(El3174AiCh, ':2')
    temperature = Cpt(El3174AiCh, ':3')
