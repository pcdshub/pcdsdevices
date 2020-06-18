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
    target_position = Cpt(EpicsSignal, ':MOVE', kind='normal')
    _target_precision = Cpt(EpicsSignal, ':MOVE.PREC', kind='config')
    _target_egu = Cpt(EpicsSignal, ':MOVE.EGU', kind='config')

    current_position = Cpt(EpicsSignalRO, ':CURPOS', kind='normal')
    _current_precision = Cpt(EpicsSignal, ':CURPOS.PREC', kind='config')
    _current_egu = Cpt(EpicsSignal, ':CURPOS.EGU', kind='config')

    status = Cpt(EpicsSignalRO, ':STATUS', kind='normal')

    _from_addr = Cpt(EpicsSignal, ':FROM_ADR', kind='config')
    _to_addr = Cpt(EpicsSignal, ':TO_ADR', kind='config')
    _save_addr = Cpt(EpicsSignal, ':SAVE', kind='config')

    _command = Cpt(EpicsSignal, ':CMD', kind='config')
    _response = Cpt(EpicsSignalRO, ':RESPONSE', kind='config')


class Ell6(EllBase):
    """
    Class for Thorlabs ELL6 2 position filter slider.
    """

    # Names for slider positions
    name_0 = Cpt(EpicsSignal, ':NAME0', kind='config')
    name_1 = Cpt(EpicsSignal, ':NAME1', kind='config')


class Ell9(Ell6):
    """
    Class for Thorlabs ELL9 4 position filter slider.
    """

    # Names for slider positions
    name_2 = Cpt(EpicsSignal, ':NAME2', kind='config')
    name_3 = Cpt(EpicsSignal, ':NAME3', kind='config')
