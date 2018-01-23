from ophyd import Component as Cmp, EpicsSignalRO

from .inout import InOutPVStatePositioner


class MovableStand(InOutPVStatePositioner):
    in_limit = Cmp(EpicsSignalRO, ':IN_DI')
    out_limit = Cmp(EpicsSignalRO, ':OUT_DO')

    _state_logic = {"in_limit": {0: "defer",
                                 1: "IN"},
                    "out_limit": {0: "defer",
                                  1: "OUT"}}

    def set(self, *args, **kwargs):
        raise NotImplementedError('Stand not motorized')
