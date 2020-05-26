"""
Classes for ThorLabs Elliptec motors.
"""


from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO


class ELL_Base(Device):
    """
    Base class for Elliptec stages.

    Sufficient for control of ELL17/20 (28/60mm linear stages) and ELL14/18
    (rotation) stages.

    Parameters
    ----------
    prefix : str
        The PV base of the stage.
    """
    _Target_Position = Cpt(EpicsSignal, ':MOVE', name='Target Position',
                           kind='normal')
    _Target_Precision = Cpt(EpicsSignal, ':MOVE.PREC', name='Target Precision',
                            kind='config')
    _Target_EGU = Cpt(EpicsSignal, ':MOVE.EGU', name='Target EGU',
                      kind='config')
    _Current_Position = Cpt(EpicsSignalRO, ':CURPOS', name='Current Position',
                            kind='normal')
    _Current_Precision = Cpt(EpicsSignal, ':CURPOS.PREC',
                             name='Current Precision', kind='config')
    _Current_EGU = Cpt(EpicsSignal, ':CURPOS.EGU', name='Current EGU',
                       kind='config')
    _Status = Cpt(EpicsSignalRO, ':STATUS', name='Status', kind='normal')
    _From_Addr = Cpt(EpicsSignal, ':FROM_ADR', name='From Address',
                     kind='config')
    _To_Addr = Cpt(EpicsSignal, ':TO_ADR', name='To Address',
                   kind='config')
    _Save_Addr = Cpt(EpicsSignal, ':SAVE', name='Save Data', kind='config')
    _Command = Cpt(EpicsSignal, ':CMD', name='Command', kind='config')
    _Response = Cpt(EpicsSignalRO, ':RESPONSE', name='Response', kind='config')


class ELL6(ELL_Base):
    """
    Class for Thorlabs ELL6 2 position filter slider.
    """

    # Names for slider positions
    _Name_0 = Cpt(EpicsSignal, ':NAME0', name='Name 0', kind='config')
    _Name_1 = Cpt(EpicsSignal, ':NAME1', name='Name 1', kind='config')


class ELL9(ELL6):
    """
    Class for Thorlabs ELL9 4 position filter slider.
    """

    # Names for slider positions
    _Name_2 = Cpt(EpicsSignal, ':NAME2', name='Name 2', kind='config')
    _Name_3 = Cpt(EpicsSignal, ':NAME3', name='Name 3', kind='config')
