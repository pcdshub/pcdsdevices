"""
Module for the SmarPod and related devices.
"""
from ophyd import PVPositioner
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO


class SmarPod(PVPositioner):
    # A base class for a SmarPod controller.
    init = Cpt(EpicsSignal, ':CMD:INIT', kind='normal')
    status = Cpt(EpicsSignal, ':CMD:ALL_STATUS', kind='normal', doc='SmarPod status code')
    # Controlling unit number
    cmd_unit = Cpt(EpicsSignal, ':CMD:UNIT', kind='normal')
    unit = Cpt(EpicsSignal, ':UNIT', kind='normal', doc='Selected SmarPod unit')
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
    # Positions - Move
    cmd_move = Cpt(EpicsSignal, ':CMD:MOVE', kind='normal')
    cmd_x = Cpt(EpicsSignal, ':CMD:X', kind='normal')
    cmd_y = Cpt(EpicsSignal, ':CMD:Y', kind='normal')
    cmd_z = Cpt(EpicsSignal, ':CMD:Z', kind='normal')
    cmd_rx = Cpt(EpicsSignal, ':CMD:RX', kind='normal')
    cmd_ry = Cpt(EpicsSignal, ':CMD:RY', kind='normal')
    cmd_rz = Cpt(EpicsSignal, ':CMD:RZ', kind='normal')
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
    x = Cpt(EpicsSignalRO, ':X', kind='normal')
    y = Cpt(EpicsSignalRO, ':Y', kind='normal')
    z = Cpt(EpicsSignalRO, ':Z', kind='normal')
    rx = Cpt(EpicsSignalRO, ':RX', kind='normal')
    ry = Cpt(EpicsSignalRO, ':RY', kind='normal')
    rz = Cpt(EpicsSignalRO, ':RZ', kind='normal')
    # Movement - Readback
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
    # Miscellaneous
    cmd_calibrate = Cpt(EpicsSignal, ':CMD:CALIBRATE', kind='normal')
    cmd_read_ver = Cpt(EpicsSignal, ':CMD:READ_VER', kind='normal')
    ver_sys = Cpt(EpicsSignalRO, ':VER:SYS', kind='omitted')
    # Device Info
    ver_sn = Cpt(EpicsSignalRO, ':VER:SN', kind='omitted')
    ver_product = Cpt(EpicsSignalRO, ':VER:PRODUCT', kind='omitted')
    ver_firmware = Cpt(EpicsSignalRO, ':VER:FIRMWARE', kind='omitted')
    # Status
    cmd_read_status = Cpt(EpicsSignal, ':CMD:READ_STATUS', kind='normal')
    status_temp = Cpt(EpicsSignalRO, ':STATUS:TEMP', kind='omitted')
    status_load = Cpt(EpicsSignalRO, ':STATUS:LOAD', kind='omitted')
    status_memory = Cpt(EpicsSignalRO, ':STATUS:MEMORY', kind='omitted')
    status_net_bytes_in = Cpt(EpicsSignalRO, ':STATUS:NET_BYTES_IN', kind='omitted')
    status_net_bytes_out = Cpt(EpicsSignalRO, ':STATUS:NET_BYTES_OUT', kind='omitted')
    status_net = Cpt(EpicsSignalRO, ':STATUS:NET', kind='omitted')
    status_status = Cpt(EpicsSignalRO, ':STATUS:STATUS', kind='omitted')
    status_bootcnt = Cpt(EpicsSignalRO, ':STATUS:BOOTCNT', kind='omitted')
    status_uptime = Cpt(EpicsSignalRO, ':STATUS:UPTIME', kind='omitted')
    status_ip = Cpt(EpicsSignalRO, ':STATUS:IP', kind='omitted')
    status_client_ip = Cpt(EpicsSignalRO, ':STATUS:CLIENT_IP', kind='omitted')
    status_ser_status = Cpt(EpicsSignalRO, ':STATUS:SER_STATUS', kind='omitted')
    status_ser_bytes_in = Cpt(EpicsSignalRO, ':STATUS:SER_BYTES_IN', kind='omitted')
    status_ser_bytes_out = Cpt(EpicsSignalRO, ':STATUS:SER_BYTES_OUT', kind='omitted')
    status_display = Cpt(EpicsSignalRO, ':STATUS:DISPLAY', kind='omitted')
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


class SmarpodPose(Device):
    pose_name = Cpt(EpicsSignal, ':NAME_RBV', write_pv=':NAME', kind='normal', doc='Pose name input')
    x = Cpt(EpicsSignal, ':X', kind='normal', doc='Pose X Position Data')
    y = Cpt(EpicsSignal, ':Y', kind='normal', doc='Pose Y Position Data')
    z = Cpt(EpicsSignal, ':Z', kind='normal', doc='Pose Z Position Data')
    rx = Cpt(EpicsSignal, ':RX', kind='normal', doc='Pose RX Position Data')
    ry = Cpt(EpicsSignal, ':RY', kind='normal', doc='Pose RY Position Data')
    rz = Cpt(EpicsSignal, ':RZ', kind='normal', doc='Pose RZ Position Data')
    record = Cpt(EpicsSignal, ':RECORD', kind='normal', doc='Fanout for pose')
    execute = Cpt(EpicsSignal, ':EXECUTE', kind='normal', doc='Enacts Pose Positions')


class Smarpod(Device):
    pose_1 = Cpt(SmarpodPose, ":POSE_1")
    pose_2 = Cpt(SmarpodPose, ":POSE_2")
    pose_3 = Cpt(SmarpodPose, ":POSE_3")
    pose_4 = Cpt(SmarpodPose, ":POSE_4")
    pose_5 = Cpt(SmarpodPose, ":POSE_5")
