"""
Module for the `IPM` intensity position monitor class
"""
from ophyd import Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO

from .doc_stubs import basic_positioner_init
from .inout import InOutRecordPositioner


class IPM(InOutRecordPositioner):
    """
    Standard intensity position monitor.

    This is an `InOutRecordPositioner` that moves
    the target position to any of the four set positions, or out. Valid states
    are (1, 2, 3, 4, 5) or the equivalent
    (TARGET1, TARGET2, TARGET3, TARGET4, OUT).

    IPMs each also have a diode, which is implemented as the diode attribute of
    this class. This can easily be controlled using ``ipm.diode.insert()`` or
    ``ipm.diode.remove()``.
    """
    __doc__ += basic_positioner_init

    state = Cpt(EpicsSignal, ':TARGET', write_pv=':TARGET:GO')
    diode = Cpt(InOutRecordPositioner, ':DIODE')
    readback = FCpt(EpicsSignalRO, '{self.prefix}:TARGET:{self._readback}')

    in_states = ['TARGET1', 'TARGET2', 'TARGET3', 'TARGET4']
    states_list = in_states + ['OUT']

    # Assume that having any target in gives transmission 0.8
    _transmission = {st: 0.8 for st in in_states}
