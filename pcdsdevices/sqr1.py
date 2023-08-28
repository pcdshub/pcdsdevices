"""
    Ophyd class for square-one tri-sphere motion system
    (https://www.sqr-1.com/tsp.html)
"""

import logging

from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositionerIsClose
from ophyd.signal import EpicsSignal
from ophyd.status import AndStatus
from ophyd.status import wait as status_wait

logger = logging.getLogger(__name__)


class SQR1Axis(PVPositionerIsClose):
    setpoint = FCpt(EpicsSignal, '{prefix}:TARGET:{_axis}', kind='normal')
    readback = FCpt(EpicsSignal, '{prefix}:TARGET:{_axis}:RBV', kind='hinted')
    actuate = FCpt(EpicsSignal, '{prefix}:MOV', kind='normal')
    actuate_value = 1
    stop_signal = FCpt(EpicsSignal, '{prefix}:KILL', kind='normal')
    stop_value = 1

    def __init__(self,
                 prefix,
                 axis,
                 sync_setpoints=None,
                 **kwargs
                 ):
        self.prefix = prefix
        self._axis = axis  # axis values {X, Y, Z, rX, rY, rZ}
        self._sync_setpoints = sync_setpoints
        super().__init__(prefix, **kwargs)

    def move(self,
             position,
             wait=True,
             timeout=None,
             moved_cb=None,
             sync_rb=True
             ):
        if sync_rb and self._sync_setpoints:
            self._sync_setpoints()
        return super().move(position, wait, timeout, moved_cb)


class SQR1(Device):
    x = FCpt(SQR1Axis, '{prefix}', axis="X", rtol=0.001)
    y = FCpt(SQR1Axis, '{prefix}', axis="Y", rtol=0.001)
    z = FCpt(SQR1Axis, '{prefix}', axis="Z", rtol=0.001)
    rx = FCpt(SQR1Axis, '{prefix}', axis="rX", rtol=0.001)
    ry = FCpt(SQR1Axis, '{prefix}', axis="rY", rtol=0.001)
    rz = FCpt(SQR1Axis, '{prefix}', axis="rZ", rtol=0.001)

    def __init__(self,
                 prefix="",
                 *,
                 name,
                 kind=None,
                 read_attrs=None,
                 configuration_attrs=None,
                 parent=None,
                 **kwargs):
        super().__init__(prefix,
                         name=name,
                         kind=kind,
                         read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         parent=parent,
                         **kwargs
                         )
        self.x._sync_setpoints = self.sync_setpoints
        self.y._sync_setpoints = self.sync_setpoints
        self.z._sync_setpoints = self.sync_setpoints
        self.rx._sync_setpoints = self.sync_setpoints
        self.ry._sync_setpoints = self.sync_setpoints
        self.rz._sync_setpoints = self.sync_setpoints

    def sync_setpoints(self):
        print("sync_setpoint")
        self.x.setpoint.put(self.x.readback.get())
        self.y.setpoint.put(self.y.readback.get())
        self.z.setpoint.put(self.z.readback.get())
        self.rx.setpoint.put(self.rx.readback.get())
        self.ry.setpoint.put(self.ry.readback.get())
        self.rz.setpoint.put(self.rz.readback.get())

    def multi_axis_move(self,
                        x_sp=None,
                        y_sp=None,
                        z_sp=None,
                        rx_sp=None,
                        ry_sp=None,
                        rz_sp=None,
                        wait=True,
                        timeout=10.0
                        ):
        x_sp = x_sp or self.x.readback.get()
        y_sp = y_sp or self.y.readback.get()
        z_sp = z_sp or self.z.readback.get()
        rx_sp = rx_sp or self.rx.readback.get()
        ry_sp = ry_sp or self.ry.readback.get()
        rz_sp = rz_sp or self.rz.readback.get()

        x_status = self.x.move(x_sp,
                               wait=False,
                               timeout=timeout,
                               sync_rb=False)
        y_status = self.y.move(y_sp,
                               wait=False,
                               timeout=timeout,
                               sync_rb=False)
        z_status = self.z.move(z_sp,
                               wait=False,
                               timeout=timeout,
                               sync_rb=False
                               )
        rx_status = self.rx.move(rx_sp,
                                 wait=False,
                                 timeout=timeout,
                                 sync_rb=False)
        ry_status = self.ry.move(ry_sp,
                                 wait=False,
                                 timeout=timeout,
                                 sync_rb=False)
        rz_status = self.rz.move(rz_sp,
                                 wait=False,
                                 timeout=timeout,
                                 sync_rb=False)

        status = AndStatus(
            x_status,
            AndStatus(y_status,
                      AndStatus(z_status,
                                AndStatus(rx_status,
                                          AndStatus(ry_status,
                                                    rz_status)))))
        return status_wait(status) if wait else status
