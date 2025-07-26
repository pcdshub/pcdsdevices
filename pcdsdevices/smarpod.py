"""
Module for the SmarPod and related devices.

SmarPod is a hexapod-like positioning system from SmarAct

> SMARPOD motion systems offer six degrees of freedom similar to classical hexapod
> systems while guaranteeing highest resolution and repeatability. Compared to
> serial kinematic systems, parallel kinematic SMARPODs exhibit a higher stiffness.
> A user-friendly software package allows easy integration into your own control environment assuring a very short setup time.

see https://www.smaract.com/en/smarpod
"""

from __future__ import annotations

import enum
import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.status import wait as status_wait

from pcdsdevices.pv_positioner import PVPositionerIsClose

logger = logging.getLogger(__name__)


class SmarPodAxisEnum(str, enum.Enum):
    """
    An enumeration representing axes available in tri-sphere table stage.

    - 'X': X-axis translation
    - 'Y': Y-axis translation
    - 'Z': Z-axis translation
    - 'RX': X-axis rotation
    - 'RY': Y-axis rotation
    - 'RZ': Z-axis rotation
    """

    X = 'X'
    Y = 'Y'
    Z = 'Z'
    RX = 'RX'
    RY = 'RY'
    RZ = 'RZ'


class SmarPodPose(Device):
    """
    The translation and orientation of the SmarPod stage is called the pose. The translation part of a pose is
    the offset of the stage in X, Y and Z direction relative to the zero position. The angles Θx, Θy and Θz
    define the rotation around the respective axis.
    """
    pose_name = Cpt(EpicsSignal, ':NAME_RBV', write_pv=':NAME', kind='normal', doc='Pose name input')
    x = Cpt(EpicsSignal, ':X', kind='normal', doc='Pose X Position Data')
    y = Cpt(EpicsSignal, ':Y', kind='normal', doc='Pose Y Position Data')
    z = Cpt(EpicsSignal, ':Z', kind='normal', doc='Pose Z Position Data')
    rx = Cpt(EpicsSignal, ':RX', kind='normal', doc='Pose RX Position Data')
    ry = Cpt(EpicsSignal, ':RY', kind='normal', doc='Pose RY Position Data')
    rz = Cpt(EpicsSignal, ':RZ', kind='normal', doc='Pose RZ Position Data')
    record = Cpt(EpicsSignal, ':RECORD', kind='normal', doc='Fanout for pose')
    execute = Cpt(EpicsSignal, ':EXECUTE', kind='normal', doc='Enacts Pose Positions')


class SmarPodStatus(Device):
    """
    This class holds basic status information about the SmarPod.
    """
    temp = Cpt(EpicsSignalRO, ':TEMP', kind='omitted')
    load = Cpt(EpicsSignalRO, ':LOAD', kind='omitted')
    memory = Cpt(EpicsSignalRO, ':MEMORY', kind='omitted')
    net_bytes_in = Cpt(EpicsSignalRO, ':NET_BYTES_IN', kind='omitted')
    net_bytes_out = Cpt(EpicsSignalRO, ':NET_BYTES_OUT', kind='omitted')
    net = Cpt(EpicsSignalRO, ':NET', kind='omitted')
    status = Cpt(EpicsSignalRO, ':STATUS', kind='omitted')
    bootcnt = Cpt(EpicsSignalRO, ':BOOTCNT', kind='omitted')
    uptime = Cpt(EpicsSignalRO, ':UPTIME', kind='omitted')
    ip = Cpt(EpicsSignalRO, ':IP', kind='omitted')
    client_ip = Cpt(EpicsSignalRO, ':CLIENT_IP', kind='omitted')
    ser_status = Cpt(EpicsSignalRO, ':SER_STATUS', kind='omitted')
    ser_bytes_in = Cpt(EpicsSignalRO, ':SER_BYTES_IN', kind='omitted')
    ser_bytes_out = Cpt(EpicsSignalRO, ':SER_BYTES_OUT', kind='omitted')
    display = Cpt(EpicsSignalRO, ':DISPLAY', kind='omitted')


class SmarPodAxis(PVPositionerIsClose):
    setpoint = FCpt(EpicsSignal, '{prefix}:CMD:{axis}')
    readback = FCpt(EpicsSignal, '{prefix}:{axis}')
    actuate = Cpt(EpicsSignal, ':CMD:MOVE')
    actuate_value = 0
    stop_signal = Cpt(EpicsSignal, ':CMD:STOP')
    stop_value = 0
    cmd_reachable = Cpt(EpicsSignal, ':CMD:REACHABLE', kind='normal')
    reachable = Cpt(EpicsSignalRO, ':REACHABLE')
    atol = 1E-5  # 10 nm
    csy_cmd = Cpt(EpicsSignal, ':CSY:CMD:{axis}', kind='normal')
    csy_rb = Cpt(EpicsSignalRO, ':CSY:{axis}', kind='normal')
    defer_motion : bool = False

    def __init__(self, prefix, axis: SmarPodAxisEnum, **kwargs):
        self.axis = axis.value
        return super().__init__(prefix, **kwargs)

    def _setup_move(self, position):
        '''Move and do not wait until motion is complete (asynchronous).
        Before moving check the position is reachable.'''

        logger.info('Checking if position is reachable')
        self.setpoint.put(position, wait=True)
        is_reachable = self.reachable.get()

        logger.info(f"is_reachable : {is_reachable}")
        if not is_reachable:
            raise ValueError('Position is unreachable !!!')
        if self.actuate and not self.defer_motion:
            logger.debug('%s.actuate=%s', self.name, self.actuate_value)
            self.actuate.put(self.actuate_value, wait=False)


class SmarPod(Device):
    """
    SmarPod is a hexapod-like positioning system from SmarAct
    """
    # A base class for a SmarPod controller.
    init = Cpt(EpicsSignal, ':CMD:INIT', kind='normal')
    status = Cpt(EpicsSignal, ':CMD:ALL_STATUS', kind='normal', doc='SmarPod status code')
    # Controlling unit number
    cmd_unit = Cpt(EpicsSignal, ':CMD:UNIT', kind='normal')
    unit = Cpt(EpicsSignal, ':UNIT', kind='normal', doc='Selected SmarPod unit')
    # Device Info
    ver_sn = Cpt(EpicsSignalRO, ':VER:SN', kind='omitted')
    ver_product = Cpt(EpicsSignalRO, ':VER:PRODUCT', kind='omitted')
    ver_firmware = Cpt(EpicsSignalRO, ':VER:FIRMWARE', kind='omitted')
    # Reference
    cmd_ref = Cpt(EpicsSignal, ':CMD:REF', kind='normal')
    ref = Cpt(EpicsSignalRO, ':REF', kind='normal', doc='Readback referenced state')
    _ref = Cpt(EpicsSignal, ':_REF', kind='normal', doc='Async reference response')
    cmd_ref_method = Cpt(EpicsSignal, ':CMD:REF_METHOD', kind='normal', doc='Set reference method')
    ref_method = Cpt(EpicsSignalRO, ':REF_METHOD', kind='normal', doc='Readback reference method')
    cmd_ref_x_direct = Cpt(EpicsSignal, ':CMD:REF_X_DIRECT', kind='normal', doc='Set reference x-direction')
    ref_x_direct = Cpt(EpicsSignalRO, ':REF_X_DIRECT', kind='normal', doc='Readback reference x-direction')
    cmd_ref_y_direct = Cpt(EpicsSignal, ':CMD:REF_Y_DIRECT', kind='normal', doc='Set reference y-direction')
    ref_y_direct = Cpt(EpicsSignalRO, ':REF_Y_DIRECT', kind='normal', doc='Readback reference y-direction')
    cmd_ref_z_direct = Cpt(EpicsSignal, ':CMD:REF_Z_DIRECT', kind='normal', doc='Set reference z-direction')
    ref_z_direct = Cpt(EpicsSignalRO, ':REF_Z_DIRECT', kind='normal', doc='Readback reference z-direction')

    # Stop
    cmd_stop = Cpt(EpicsSignal, ':CMD:STOP', kind='normal', doc='Stops SmarPod Movements')
    # Pose reachable?
    cmd_reachable = Cpt(EpicsSignal, ':CMD:REACHABLE', kind='normal')
    reachable = Cpt(EpicsSignalRO, ':REACHABLE', kind='normal', doc='Test if the SP can reach a pose. Does not move the SP')
    # Positions - Readback
    cmd_pos_rbv = Cpt(EpicsSignal, ':CMD:POS_RBV', kind='normal', doc='Readback current pose position')
    x_m = Cpt(EpicsSignalRO, ':X_M', kind='normal')
    y_m = Cpt(EpicsSignalRO, ':Y_M', kind='normal')
    z_m = Cpt(EpicsSignalRO, ':Z_M', kind='normal')
    # Movement - Readback
    cmd_move = Cpt(EpicsSignal, ':CMD:MOVE', kind='normal')
    moving = Cpt(EpicsSignal, ':MOVING', kind='normal', doc='Movement status')
    # Movement - Sync
    cmd_sync = Cpt(EpicsSignal, ':CMD:SYNC', kind='normal')
    error_code = Cpt(EpicsSignalRO, ':ERROR_CODE', kind='normal')
    error_desc = Cpt(EpicsSignalRO, ':ERROR_DESC', kind='normal')
    # Pivot-point
    cmd_pivot_rbv = Cpt(EpicsSignal, ':CMD:PIVOT_RBV', kind='normal', doc='Readback pivot point')
    cmd_set_pivot = Cpt(EpicsSignal, ':CMD:SET_PIVOT', kind='normal')
    cmd_sync_pivot = Cpt(EpicsSignal, ':CMD:SYNC_PIVOT', kind='normal')
    cmd_pivot_mode = Cpt(EpicsSignal, ':CMD:PIVOT_MODE', kind='normal')
    pivot_mode = Cpt(EpicsSignal, ':PIVOT_MODE', kind='normal', doc='Pivot mode')
    # Pivot positions
    px_m = Cpt(EpicsSignal, ':PX_M', kind='normal')
    py_m = Cpt(EpicsSignal, ':PY_M', kind='normal')
    pz_m = Cpt(EpicsSignal, ':PZ_M', kind='normal')
    px = Cpt(EpicsSignal, ':PX', kind='normal')
    py = Cpt(EpicsSignal, ':PY', kind='normal')
    pz = Cpt(EpicsSignal, ':PZ', kind='normal')
    # Pivot request positions
    cmd_px = Cpt(EpicsSignal, ':CMD:PX', kind='normal')
    cmd_py = Cpt(EpicsSignal, ':CMD:PY', kind='normal')
    cmd_pz = Cpt(EpicsSignal, ':CMD:PZ', kind='normal')
    # axes
    x = Cpt(SmarPodAxis, '', axis=SmarPodAxisEnum.Y, egu='mm', kind='normal')
    y = Cpt(SmarPodAxis, '', axis=SmarPodAxisEnum.Z, egu='mm', kind='normal')
    z = Cpt(SmarPodAxis, '', axis=SmarPodAxisEnum.X, egu='mm', kind='normal')
    rx = Cpt(SmarPodAxis, '', axis=SmarPodAxisEnum.RY, egu='deg', kind='normal')
    ry = Cpt(SmarPodAxis, '', axis=SmarPodAxisEnum.RZ, egu='deg', kind='normal')
    rz = Cpt(SmarPodAxis, '', axis=SmarPodAxisEnum.RX, egu='deg', kind='normal')
    # Sensor mode
    cmd_sensor_mode = Cpt(EpicsSignal, ':CMD:SENSOR_MODE', kind='normal')
    sensor_mode = Cpt(EpicsSignal, ':SENSOR_MODE', kind='normal', doc='Sensor mode')
    # Maximum frequency
    cmd_freq = Cpt(EpicsSignal, ':CMD:FREQ', kind='normal')
    freq = Cpt(EpicsSignal, ':FREQ', kind='normal')
    # Maximum velocity
    cmd_vel = Cpt(EpicsSignal, ':CMD:VEL', kind='normal', doc='sets movement velocity')
    vel = Cpt(EpicsSignal, ':VEL', kind='normal', doc='current speed-control and speed settings')
    # Maximum acceleration
    cmd_accel = Cpt(EpicsSignal, ':CMD:ACCEL', kind='normal', doc='sets movement acceleration')
    accel = Cpt(EpicsSignal, ':ACCEL', kind='normal', doc='current acceleration-control and acceleration settings')
    # Read and Set Poses, Pose 1-5:
    pose_1 = Cpt(SmarPodPose, ':POSE_1')
    pose_2 = Cpt(SmarPodPose, ':POSE_2')
    pose_3 = Cpt(SmarPodPose, ':POSE_3')
    pose_4 = Cpt(SmarPodPose, ':POSE_4')
    pose_5 = Cpt(SmarPodPose, ':POSE_5')
    # Status
    cmd_read_status = Cpt(EpicsSignal, ':CMD:READ_STATUS', kind='normal')
    status = Cpt(SmarPodStatus, ":STATUS")
    # Miscellaneous
    cmd_calibrate = Cpt(EpicsSignal, ':CMD:CALIBRATE', kind='normal')
    cmd_read_ver = Cpt(EpicsSignal, ':CMD:READ_VER', kind='normal')
    ver_sys = Cpt(EpicsSignalRO, ':VER:SYS', kind='omitted')
    # coordinate offset
    csy_set = Cpt(EpicsSignal, ':CSY:SET', kind='normal', doc="set csy offset")
    csy_zero = Cpt(EpicsSignal, ':CMD:SPZ', kind='normal', doc="set csy to zero")

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

        self.x.defer_motion = True
        self.y.defer_motion = True
        self.z.defer_motion = True
        self.rx.defer_motion = True
        self.ry.defer_motion = True
        self.rz.defer_motion = True

        self.x.setpoint.put(x_sp)
        self.y.setpoint.put(y_sp)
        self.z.setpoint.put(z_sp)
        self.rx.setpoint.put(rx_sp)
        self.ry.setpoint.put(ry_sp)
        self.rz.setpoint.put(rz_sp)

        x_status = self.x.move(x_sp, wait=False, timeout=timeout)
        y_status = self.y.move(y_sp, wait=False, timeout=timeout)
        z_status = self.z.move(z_sp, wait=False, timeout=timeout)
        rx_status = self.rx.move(rx_sp, wait=False, timeout=timeout)
        ry_status = self.ry.move(ry_sp, wait=False, timeout=timeout)
        rz_status = self.rz.move(rz_sp, wait=False, timeout=timeout)

        self.cmd_move.put(0)

        status = x_status & y_status & z_status & rx_status & \
            ry_status & rz_status
        if wait:
            status_wait(status)

        self.x.defer_motion = False
        self.y.defer_motion = False
        self.z.defer_motion = False
        self.rx.defer_motion = False
        self.ry.defer_motion = False
        self.rz.defer_motion = False

        return status
