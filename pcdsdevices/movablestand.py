"""
Module for stands that can be moved
"""
from ophyd import Component as Cpt, EpicsSignalRO

from .inout import InOutPVStatePositioner


class MovableStand(InOutPVStatePositioner):
    """
    Stand that can be moved.

    Parameters
    ----------
    prefix: ``str``

    name: ``str``, required keyword
    """
    in_limit = Cpt(EpicsSignalRO, ':IN_DI', kind='normal')
    out_limit = Cpt(EpicsSignalRO, ':OUT_DO', kind='normal')

    _state_logic = {"in_limit": {0: "defer",
                                 1: "IN"},
                    "out_limit": {0: "defer",
                                  1: "OUT"}}

    def set(self, *args, **kwargs):
        raise NotImplementedError('Stand not motorized')
