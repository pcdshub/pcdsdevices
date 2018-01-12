from ophyd import Component, EpicsSignalRO

from ..state import PVStatePositioner


class MovableStand(PVStatePositioner):
    in_limit = Component(EpicsSignalRO, ':IN_DI')
    out_limit = Component(EpicsSignalRO, ':OUT_DO')

    _state_logic = {"in_limit": {0: "defer",
                                 1: "IN"},
                    "out_limit": {0: "defer",
                                  1: "OUT"}}
