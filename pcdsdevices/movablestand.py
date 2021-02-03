"""
Module for stands that can be moved.
"""
from ophyd import Component as Cpt
from ophyd import EpicsSignalRO

from .inout import InOutPVStatePositioner


class MovableStand(InOutPVStatePositioner):
    """
    Stand that can be moved.

    Parameters
    ----------
    prefix : str
        Base PV for the stand.

    name : str
        Name to call the stand by.
    """

    in_limit = Cpt(EpicsSignalRO, ':IN_DI', kind='normal')
    out_limit = Cpt(EpicsSignalRO, ':OUT_DO', kind='normal')

    _state_logic = {"in_limit": {0: "defer",
                                 1: "IN"},
                    "out_limit": {0: "defer",
                                  1: "OUT"}}

    def set(self, *args, **kwargs):
        raise NotImplementedError('Stand not motorized')

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
