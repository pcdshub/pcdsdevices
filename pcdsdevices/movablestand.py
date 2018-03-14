"""
Module for stands that can be moved
"""
from ophyd import Component as Cmp, EpicsSignalRO

from .inout import InOutPVStatePositioner


class MovableStand(InOutPVStatePositioner):
    """
    Stand that can be moved.

    Parameters
    ----------
    prefix: ``str``

    name: ``str``, required keyword
    """
    in_limit = Cmp(EpicsSignalRO, ':IN_DI')
    out_limit = Cmp(EpicsSignalRO, ':OUT_DO')

    _state_logic = {"in_limit": {0: "defer",
                                 1: "IN"},
                    "out_limit": {0: "defer",
                                  1: "OUT"}}

    def set(self, *args, **kwargs):
        raise NotImplementedError('Stand not motorized')
