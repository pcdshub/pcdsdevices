"""
    Ophyd class for square-one tri-sphere motion system
    (https://www.sqr-1.com/tsp.html)
"""

import logging

from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositionerIsClose
from ophyd.signal import EpicsSignal, EpicsSignalRO

logger = logging.getLogger(__name__)


class SQR1Axis(PVPositionerIsClose):
    setpoint = FCpt(EpicsSignal, '{self.prefix}:TARGET:{_axis}', kind='normal')
    readback = FCpt(EpicsSignal, '{self.prefix}:TARGET:{self._axis}:RBV', kind='hinted')
    actuate = FCpt(EpicsSignal, '{self.prefix}:MOV', kind='normal')
    actuate_value = 1
    stop_signal = FCpt(EpicsSignal, '{self.prefix}:KILL', kind='normal')
    stop_value = 1

    llm = FCpt(EpicsSignalRO, '{self.prefix}:TARGET:{self._axis}:LLM', kind='normal')
    hlm = FCpt(EpicsSignalRO, '{self.prefix}:TARGET:{self._axis}:HLM', kind='normal')

    def __init__(self, prefix, axis, **kwargs):
        self._axis = axis  # axis values {X, Y, Z, rX, rY, rZ}
        super().__init__(prefix, **kwargs)

    def move(self, position, wait=True, timeout=None, moved_cb=None):
        return super().move(position, wait, timeout, moved_cb)

    def check_value(self, pos):
        self._limits = (((self.llm.get(), self.hlm.get())))
        super().check_value(pos)


class SQR1(Device):
    move = FCpt(EpicsSignal, '{self.prefix}:MOV', kind='normal')

    def __init__(self, prefix, name, **kwargs) -> None:
        super().__init__(prefix, name=name, **kwargs)
        self.x = SQR1Axis(axis="X", prefix=prefix, name=f"{name}_x", rtol=0.01)
        self.y = SQR1Axis(axis="Y", prefix=prefix, name=f"{name}_y", rtol=0.01)
        self.z = SQR1Axis(axis="Z", prefix=prefix, name=f"{name}_z", rtol=0.01)
        self.rx = SQR1Axis(axis="rX", prefix=prefix, name=f"{name}_rx", rtol=0.01)
        self.ry = SQR1Axis(axis="rY", prefix=prefix, name=f"{name}_ry", rtol=0.01)
        self.rz = SQR1Axis(axis="rZ", prefix=prefix, name=f"{name}_rz", rtol=0.01)

    def sync_setpoints(self):
        self.x.setpoint.put(self.x.readback.get())
        self.y.setpoint.put(self.y.readback.get())
        self.z.setpoint.put(self.z.readback.get())
        self.rx.setpoint.put(self.rx.readback.get())
        self.ry.setpoint.put(self.ry.readback.get())
        self.rz.setpoint.put(self.rz.readback.get())

    def multi_axis_move(self, x_sp=None, y_sp=None, z_sp=None, rx_sp=None, ry_sp=None, rz_sp=None):
        x_sp = x_sp or self.x.readback.get()
        y_sp = y_sp or self.y.readback.get()
        z_sp = z_sp or self.z.readback.get()
        rx_sp = rx_sp or self.rx.readback.get()
        ry_sp = ry_sp or self.ry.readback.get()
        rz_sp = rz_sp or self.rz.readback.get()

        self.x.setpoint.put(x_sp)
        self.y.setpoint.put(y_sp)
        self.z.setpoint.put(z_sp)
        self.rx.setpoint.put(rx_sp)
        self.ry.setpoint.put(ry_sp)
        self.rz.setpoint.put(rz_sp)

        self.move.put(1)
