"""
Module for the `IPM` intensity position monitor class
"""
from ophyd.device import Device, Component as Cpt

from .doc_stubs import basic_positioner_init, insert_remove
from .inout import InOutRecordPositioner


class IPMTarget(InOutRecordPositioner):
    """
    Target of a standard intensity position monitor.

    This is an `InOutRecordPositioner` that moves
    the target position to any of the four set positions, or out. Valid states
    are (1, 2, 3, 4, 5) or the equivalent
    (TARGET1, TARGET2, TARGET3, TARGET4, OUT).
    """
    __doc__ += basic_positioner_init

    in_states = ['TARGET1', 'TARGET2', 'TARGET3', 'TARGET4']
    states_list = in_states + ['OUT']

    # Assume that having any target in gives transmission 0.8
    _transmission = {st: 0.8 for st in in_states}


class IPM(Device):
    """
    Standard intensity position monitor.

    This contains two state devices, a target and a diode.
    """
    target = Cpt(IPMTarget, ':TARGET', kind='hinted')
    diode = Cpt(InOutRecordPositioner, ':DIODE', kind='omitted')

    # QIcon for UX
    _icon = 'ei.screenshot'

    tab_whitelist = ['target', 'diode']

    @property
    def inserted(self):
        """Returns ``True`` if target is inserted. Diode never blocks."""
        return self.target.inserted

    @property
    def removed(self):
        """Returns ``True`` if target is removed. Diode never blocks."""
        return self.target.removed

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the target out of the beam. Diode never blocks."""
        return self.target.remove(moved_cb=moved_cb,
                                  timeout=timeout,
                                  wait=wait)

    remove.__doc__ += insert_remove

    @property
    def transmission(self):
        """Returns the target's transmission value. Diode never blocks."""
        return self.target.transmission
