"""
    Ophyd class for square-one tri-sphere motion system
    (https://www.sqr-1.com/tsp.html)
"""

import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositionerIsClose
from ophyd.signal import EpicsSignal
from ophyd.status import wait as status_wait

logger = logging.getLogger(__name__)


class SQR1Axis(PVPositionerIsClose):
    setpoint = FCpt(EpicsSignal, '{prefix}:TARGET:{_axis}', kind='normal')
    readback = FCpt(EpicsSignal, '{prefix}:TARGET:{_axis}:RBV', kind='hinted')
    actuate = FCpt(EpicsSignal, '{prefix}:MOV', kind='normal')
    actuate_value = 1
    stop_signal = FCpt(EpicsSignal, '{prefix}:KILL', kind='normal')
    stop_value = 1

    def move(self,
             position: float,
             wait: bool = True,
             timeout: float = None,
             moved_cb: float = None,
             sync_enable: bool = True,
             ):
        if sync_enable and self._sync_setpoints:
            self._sync_setpoints()
        return super().move(position, wait, timeout, moved_cb)


class SQR1(Device):
    x = Cpt(SQR1Axis, '{prefix}', axis="X", rtol=0.001)
    y = Cpt(SQR1Axis, '{prefix}', axis="Y", rtol=0.001)
    z = Cpt(SQR1Axis, '{prefix}', axis="Z", rtol=0.001)
    rx = Cpt(SQR1Axis, '{prefix}', axis="rX", rtol=0.001)
    ry = Cpt(SQR1Axis, '{prefix}', axis="rY", rtol=0.001)
    rz = Cpt(SQR1Axis, '{prefix}', axis="rZ", rtol=0.001)
    stop_signal = Cpt(EpicsSignal, '{prefix}:KILL', kind='normal')

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
        logger.debug("sync_setpoint")
        self.x.setpoint.put(self.x.readback.get())
        self.y.setpoint.put(self.y.readback.get())
        self.z.setpoint.put(self.z.readback.get())
        self.rx.setpoint.put(self.rx.readback.get())
        self.ry.setpoint.put(self.ry.readback.get())
        self.rz.setpoint.put(self.rz.readback.get())

    def multi_axis_move(self,
                        x_sp: float = None,
                        y_sp: float = None,
                        z_sp: float = None,
                        rx_sp: float = None,
                        ry_sp: float = None,
                        rz_sp: float = None,
                        wait: bool = True,
                        timeout: float = 10.0
                        ):
        x_sp = self.x.readback.get() if x_sp is None else x_sp
        y_sp = self.y.readback.get() if y_sp is None else y_sp
        z_sp = self.z.readback.get() if z_sp is None else z_sp
        rx_sp = self.rx.readback.get() if rx_sp is None else rx_sp
        ry_sp = self.ry.readback.get() if ry_sp is None else ry_sp
        rz_sp = self.rz.readback.get() if rz_sp is None else rz_sp

        x_status = self.x.move(x_sp,
                               wait=False,
                               timeout=timeout,
                               sync_enable=False)
        y_status = self.y.move(y_sp,
                               wait=False,
                               timeout=timeout,
                               sync_enable=False)
        z_status = self.z.move(z_sp,
                               wait=False,
                               timeout=timeout,
                               sync_enable=False
                               )
        rx_status = self.rx.move(rx_sp,
                                 wait=False,
                                 timeout=timeout,
                                 sync_enable=False)
        ry_status = self.ry.move(ry_sp,
                                 wait=False,
                                 timeout=timeout,
                                 sync_enable=False)
        rz_status = self.rz.move(rz_sp,
                                 wait=False,
                                 timeout=timeout,
                                 sync_enable=False)

        status = x_status & y_status & z_status & rx_status & +\
            ry_status & rz_status

        return status_wait(status) if wait else status

    def stop(self):
        self.stop_signal.put(1)
