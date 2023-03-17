"""
Ophyd class for square-one tri-sphere motion system (https://www.sqr-1.com/tsp.html)
"""

from ophyd.pv_positioner import PVPositionerIsClose
from ophyd.device import FormattedComponent as FCpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

import logging

logger = logging.getLogger(__name__)


class SQR1Axis(PVPositionerIsClose):
    setpoint = FCpt(EpicsSignal, '{self.prefix}:TARGET:{self._axis}', kind='normal')
    readback = FCpt(EpicsSignal, '{self.prefix}:TARGET:{self._axis}:RBV', kind='normal')
    actuate = FCpt(EpicsSignal, '{self.prefix}:MOV', kind='normal')
    actuate_value = 1
    stop_signal = FCpt(EpicsSignal, '{self.prefix}:KILL', kind='normal')
    stop_value = 1

    llm = FCpt(EpicsSignalRO, '{self.prefix}:TARGET:{self._axis}:LLM', kind='normal')
    hlm = FCpt(EpicsSignalRO, '{self.prefix}:TARGET:{self._axis}:HLM', kind='normal')

    def __init__(self, axis, **kwargs):
        self._axis = axis  # axis values {X,Y,Z,rX, rY, rZ}
        super().__init__(**kwargs)

        self.setpoint.put(self.readback.get())  # sync position setpoint with readback
        self._limits = ((self.llm.get(), self.hlm.get()))


class SQR1(Device):
    def __init__(self, prefix, name) -> None:
        self.prefix = prefix
        self.name = name
        self.x = SQR1Axis(axis="X", prefix=prefix, name=f"{name}_x", rtol=0.01)
        self.y = SQR1Axis(axis="Y", prefix=prefix, name=f"{name}_y", rtol=0.01)
        self.z = SQR1Axis(axis="Z", prefix=prefix, name=f"{name}_z", rtol=0.01)
        self.rx = SQR1Axis(axis="rX", prefix=prefix, name=f"{name}_rx", rtol=0.01)
        self.ry = SQR1Axis(axis="rY", prefix=prefix, name=f"{name}_ry", rtol=0.01)
        self.rz = SQR1Axis(axis="rZ", prefix=prefix, name=f"{name}_rz", rtol=0.01)
