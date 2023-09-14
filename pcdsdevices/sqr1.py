"""
Ophyd class for square-one tri-sphere motion system
(https://www.sqr-1.com/tsp.html)

This module defines Ophyd (python based hardware abstraction and
interfacing library) classes for controlling a square-one tri-sphere motion
system. The motion system consists of multiple axes, each of which can be
controlled individually. The axes include X, Y, Z, rX, rY, and rZ.

Classes:
- SQR1Axis: A class representing a single axis of the tri-sphere motion system.
It inherits from PVPositionerIsClose and includes attributes for setpoint,
readback, actuation, and stopping the motion.

- SQR1: A class representing the entire tri-sphere motion system.
It is a Device that aggregates multiple SQR1Axis instances for each axis.
It also includes methods for multi-axis movement and stopping the motion.
"""

from __future__ import annotations

import enum
import logging
import typing

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositionerIsClose
from ophyd.signal import EpicsSignal
from ophyd.status import wait as status_wait

logger = logging.getLogger(__name__)


class Axis(str, enum.Enum):
    """
    An enumeration representing axes available in tri-sphere table stage.
    This enumeration defines the following axes:
    - `X`: X-axis translation
    - `Y`: Y-axis translation
    - `Z`: Z-axis translation
    - `rX`: X-axis rotation
    - `rY`: Y-axis rotation
    - `rZ`: Z-axis rotation
    """

    X = "X"
    Y = "Y"
    Z = "Z"
    rX = "rX"
    rY = "rY"
    rZ = "rZ"


class SQR1Axis(PVPositionerIsClose):
    """
    This class represents and controls a single axis of the square-one
    tri-sphere motion system using EPICS PVs (Process Variables).
    It is a subclass of PVPositionerIsClose and includes attributes for setting
    the setpoint, reading back the current position,
    actuating the motion, and stopping the motion.

    Attributes:
        setpoint (EpicsSignal): An EPICS signal for setting the desired
        position of the axis.
        readback (EpicsSignal): An EPICS signal for reading back the current
        position of the axis.
        actuate (EpicsSignal): An EPICS signal for initiating the motion of
        the axis.
        actuate_value (any, optional): The value to be set on the 'actuate'
        signal to initiate motion (default is 1).
        stop_signal (EpicsSignal): An EPICS signal for stopping the motion of
        the axis.
        stop_value (any, optional): The value to be set on the 'stop_signal'
        to stop motion (default is 1).

    Args:
        prefix (str): The EPICS PV prefix for this axis.
        axis (str): The axis identifier ('X', 'Y', 'Z', 'rX', 'rY', 'rZ').
        sync_setpoints (callable or None): A callback function to synchronize
            setpoints before moving the axis (default is None).
        **kwargs: Additional keyword arguments to pass to the base class
        constructor.

    Methods:
        move(position,
             wait=True,
             timeout=None,
             moved_cb=None,
             sync_enable=True
             ):
            Move the axis to the specified position.

    Example:
        >>> axis_x = SQR1Axis(prefix="SQR1:AXIS_X", axis="X")
        >>> axis_x.move(5.0)  # Move the X-axis to position 5.0
    """

    setpoint = FCpt(EpicsSignal, "{prefix}:TARGET:{_axis}", kind="normal")
    readback = FCpt(EpicsSignal, "{prefix}:TARGET:{_axis}:RBV", kind="hinted")
    actuate = Cpt(EpicsSignal, ":MOV", kind="normal")
    actuate_value = 1
    stop_signal = Cpt(EpicsSignal, ":KILL", kind="normal")
    stop_value = 1

    def __init__(
        self,
        prefix: str,
        axis: Axis,
        sync_setpoints: typing.Callable | None = None,
        **kwargs,
    ):
        self._axis = axis.value
        self._sync_setpoints = sync_setpoints
        super().__init__(prefix, **kwargs)

    def move(
        self,
        position: float,
        wait: bool = True,
        timeout: float = None,
        moved_cb: typing.Callable | None = None,
        sync_enable: bool = True,
    ):
        if sync_enable and self._sync_setpoints:
            self._sync_setpoints()
        return super().move(position, wait, timeout, moved_cb)


class SQR1(Device):
    """
    This class represents the entire square-one tri-sphere motion system,
    which consists of multiple axes (X, Y, Z, rX, rY, rZ) that can be
    controlled individually. It aggregates instances of the `SQR1Axis` class
    for each axis and provides methods for multi-axis movement and
    stopping the motion.

    Attributes:
        x (SQR1Axis): An instance of the `SQR1Axis` class representing
                      the X-axis.
        y (SQR1Axis): An instance of the `SQR1Axis` class representing
                      the Y-axis.
        z (SQR1Axis): An instance of the `SQR1Axis` class representing
                      the Z-axis.
        rx (SQR1Axis): An instance of the `SQR1Axis` class representing
                       the rX-axis.
        ry (SQR1Axis): An instance of the `SQR1Axis` class representing
                       the rY-axis.
        rz (SQR1Axis): An instance of the `SQR1Axis` class representing
                       the rZ-axis.
        stop_signal (EpicsSignal): An EPICS signal for stopping the motion of
                                   the entire tri-sphere motion system.

    Args:
        prefix (str): The EPICS PV prefix for the motion system.
        name (str): The name for this device.
        kind (str or None, optional): The kind of device
                                      (e.g., 'detector', 'motor').
        read_attrs (list or None, optional): List of attribute names to be
                                             read when reading this device.
        configuration_attrs (list or None, optional): List of attribute names
                                                      to be configured when
                                                      configuring this device.
        parent (Device or None, optional): The parent device, if applicable.
        **kwargs: Additional keyword arguments to pass to the base
                  class constructor.

    Methods:
        sync_setpoints(): Synchronize the setpoints of all axes to their
        respective readback values.
        multi_axis_move(x_sp=None,
                        y_sp=None,
                        z_sp=None,
                        rx_sp=None,
                        ry_sp=None,
                        rz_sp=None,
                        wait=True,
                        timeout=10.0):Move multiple axes simultaneously
        to specified setpoints.
        stop(): Stop the motion of the entire tri-sphere motion system.

    Example:
        >>> tri_sphere = SQR1(prefix="SQR1:", name="tri_sphere")
        >>> tri_sphere.multi_axis_move(x_sp=1.0, y_sp=2.0, z_sp=3.0)
        >>> tri_sphere.stop()
    """

    x = Cpt(SQR1Axis, "", axis=Axis.X, rtol=0.001)
    y = Cpt(SQR1Axis, "", axis=Axis.Y, rtol=0.001)
    z = Cpt(SQR1Axis, "", axis=Axis.Z, rtol=0.001)
    rx = Cpt(SQR1Axis, "", axis=Axis.rX, rtol=0.001)
    ry = Cpt(SQR1Axis, "", axis=Axis.rY, rtol=0.001)
    rz = Cpt(SQR1Axis, "", axis=Axis.rZ, rtol=0.001)
    actuate = Cpt(EpicsSignal, ":MOV", kind="normal")
    actuate_value = 1
    stop_signal = Cpt(EpicsSignal, ":KILL", kind="normal")
    stop_value = 1

    def __init__(
        self,
        prefix="",
        *,
        name,
        kind=None,
        read_attrs=None,
        configuration_attrs=None,
        parent=None,
        **kwargs,
    ):
        super().__init__(
            prefix,
            name=name,
            kind=kind,
            read_attrs=read_attrs,
            configuration_attrs=configuration_attrs,
            parent=parent,
            **kwargs,
        )
        self.x._sync_setpoints = self.sync_setpoints
        self.y._sync_setpoints = self.sync_setpoints
        self.z._sync_setpoints = self.sync_setpoints
        self.rx._sync_setpoints = self.sync_setpoints
        self.ry._sync_setpoints = self.sync_setpoints
        self.rz._sync_setpoints = self.sync_setpoints

    def sync_setpoints(self):
        """
        This method has to be called at tri-sphere motion system startup to
        synchronize the setpoints of multiple axes with their respective
        readback values to avoid moving uninitialized axes to
        zero unintentionally.
        """
        logger.debug("sync_setpoint")
        self.x.setpoint.put(self.x.readback.get())
        self.y.setpoint.put(self.y.readback.get())
        self.z.setpoint.put(self.z.readback.get())
        self.rx.setpoint.put(self.rx.readback.get())
        self.ry.setpoint.put(self.ry.readback.get())
        self.rz.setpoint.put(self.rz.readback.get())

    def multi_axis_move(
        self,
        x_sp: float | None = None,
        y_sp: float | None = None,
        z_sp: float | None = None,
        rx_sp: float | None = None,
        ry_sp: float | None = None,
        rz_sp: float | None = None,
        wait: bool = True,
        timeout: float = 30.0,
    ):
        x_sp = self.x.readback.get() if x_sp is None else x_sp
        y_sp = self.y.readback.get() if y_sp is None else y_sp
        z_sp = self.z.readback.get() if z_sp is None else z_sp
        rx_sp = self.rx.readback.get() if rx_sp is None else rx_sp
        ry_sp = self.ry.readback.get() if ry_sp is None else ry_sp
        rz_sp = self.rz.readback.get() if rz_sp is None else rz_sp

        x_status = self.x.move(x_sp, wait=False, timeout=timeout,
                               sync_enable=False)
        y_status = self.y.move(y_sp, wait=False, timeout=timeout,
                               sync_enable=False)
        z_status = self.z.move(z_sp, wait=False, timeout=timeout,
                               sync_enable=False)
        rx_status = self.rx.move(rx_sp, wait=False, timeout=timeout,
                                 sync_enable=False)
        ry_status = self.ry.move(ry_sp, wait=False, timeout=timeout,
                                 sync_enable=False)
        rz_status = self.rz.move(rz_sp, wait=False, timeout=timeout,
                                 sync_enable=False)

        status = x_status & y_status & z_status & rx_status & \
            ry_status & rz_status
        if wait:
            status_wait(status)

        return status

    def stop(self):
        self.stop_signal.put(self.stop_value)
