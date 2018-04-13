"""
Module for the `IPM` intensity position monitor class
"""
from ophyd import Component as Cmp
from ophyd.signal import EpicsSignal

from .doc_stubs import basic_positioner_init
from .inout import InOutRecordPositioner


class IPM(InOutRecordPositioner):
    """
    Standard intensity position monitor.

    This is an `InOutRecordPositioner` that moves
    the target position to any of the four set positions, or out. Valid states
    are (1, 2, 3, 4, 5) or the equivalent (T1, T2, T3, T4, OUT).

    IPMs each also have a diode, which is implemented as the diode attribute of
    this class. This can easily be controlled using ``ipm.diode.insert()`` or
    ``ipm.diode.remove()``.
    """
    __doc__ += basic_positioner_init

    state = Cmp(EpicsSignal, ':TARGET', write_pv=':TARGET:GO')
    diode = Cmp(InOutRecordPositioner, ":DIODE")

    _default_settings = ['TARGET1', 'TARGET2', 'TARGET3', 'TARGET4', 'OUT']
    in_states = [1, 2, 3, 4]

    # Assume that having any target in gives transmission 0.8
    _transmission = {n: 0.8 for n in in_states}
