"""
Classes for ThorLabs Elliptec motors.
"""


from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO


class EllBase(Device):
    """
    Base class for Elliptec stages.

    Sufficient for control of ELL17/20 (28/60mm linear stages) and ELL14/18
    (rotation) stages.

    Parameters
    ----------
    prefix : str
        The PV base of the stage.
    """
    Target_Position = Cpt(EpicsSignal, ':MOVE', kind='normal')
    _Target_Precision = Cpt(EpicsSignal, ':MOVE.PREC', kind='config')
    _Target_EGU = Cpt(EpicsSignal, ':MOVE.EGU', kind='config')

    Current_Position = Cpt(EpicsSignalRO, ':CURPOS', kind='normal')
    _Current_Precision = Cpt(EpicsSignal, ':CURPOS.PREC', kind='config')
    _Current_EGU = Cpt(EpicsSignal, ':CURPOS.EGU', kind='config')

    Status = Cpt(EpicsSignalRO, ':STATUS', kind='normal')

    _From_Addr = Cpt(EpicsSignal, ':FROM_ADR', kind='config')
    _To_Addr = Cpt(EpicsSignal, ':TO_ADR', kind='config')
    _Save_Addr = Cpt(EpicsSignal, ':SAVE', kind='config')

    _Command = Cpt(EpicsSignal, ':CMD', kind='config')
    _Response = Cpt(EpicsSignalRO, ':RESPONSE', kind='config')


class Ell6(EllBase):
    """
    Class for Thorlabs ELL6 2 position filter slider.
    """

    # Names for slider positions
    Name0 = Cpt(EpicsSignal, ':NAME0', kind='config')
    Name1 = Cpt(EpicsSignal, ':NAME1', kind='config')


class Ell9(Ell6):
    """
    Class for Thorlabs ELL9 4 position filter slider.
    """

    # Names for slider positions
    Name2 = Cpt(EpicsSignal, ':NAME2', kind='config')
    Name3 = Cpt(EpicsSignal, ':NAME3', kind='config')
