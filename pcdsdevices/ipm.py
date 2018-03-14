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

    states_list = ['T1', 'T2', 'T3', 'T4', 'OUT']
    _states_alias = {'T1': ['T1', 'TARGET1', 't1', 'target1'],
                     'T2': ['T2', 'TARGET2', 't2', 'target2'],
                     'T3': ['T3', 'TARGET3', 't3', 'target3'],
                     'T4': ['T4', 'TARGET4', 't4', 'target4']}

    in_states = ['T1', 'T2', 'T3', 'T4']

    # Assume that having any target in gives transmission 0.8
    _transmission = {'T' + str(n): 0.8 for n in range(1, 5)}
