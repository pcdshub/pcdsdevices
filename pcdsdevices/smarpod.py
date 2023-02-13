"""
Module for the SmarPod and related devices.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal
from .interface import BaseInterface



class SmarPod(BaseInterface, Device):
    """
    A base class for a SmarPod controller.
    """
    init = Cpt(EpicsSignal, ':CMD:INIT', kind='normal')
    status = Cpt(EpicsSignal, ':CMD:ALL_STATUS', kind='normal')



    """
    Controlling unit number
    """
    cmd_unit = Cpt(EpicsSignal, ':CMD:UNIT', kind='normal')
    unit = Cpt(EpicsSignal, ':UNIT', kind='normal', doc='Selected SmarPod unit')



    """
    Reference
    """
    cmd_ref = Cpt(EpicsSignal, ':CMD:REF', kind='normal')
    ref = Cpt(EpicsSignal, ':REF', kind='normal', doc='Readback referenced state')
    _ref = Cpt(EpicsSignal, ':_REF', kind='normal', doc='Async reference response') 
    cmd_ref_method = Cpt(EpicsSignal, ':CMD:REF_METHOD', kind='normal', doc='Set reference method') 
    ref_method = Cpt(EpicsSignal, ':REF_METHOD', kind='normal', doc='Readback reference method') 
    cmd_ref_x_direct = Cpt(EpicsSignal, ':CMD:REF_X_DIRECT', kind='normal', doc='Set reference x-direction') 
    ref_x_direct = Cpt(EpicsSignal, ':REF_X_DIRECT', kind='normal', doc='Readback reference x-direction') 
    cmd_ref_y_direct = Cpt(EpicsSignal, ':CMD:REF_Y_DIRECT', kind='normal', doc='Set reference y-direction') 
    ref_y_direct = Cpt(EpicsSignal, ':REF_Y_DIRECT', kind='normal', doc='Readback reference y-direction') 
    cmd_ref_z_direct = Cpt(EpicsSignal, ':CMD:REF_Z_DIRECT', kind='normal', doc='Set reference z-direction') 
    ref_z_direct = Cpt(EpicsSignal, ':REF_Z_DIRECT', kind='normal', doc='Readback reference z-direction')



    """
    Positions - Move
    """
    cmd_move = Cpt(EpicsSignal, ':CMD:MOVE', kind='normal')
    cmd_x = Cpt(EpicsSignal, ':CMD:X', kind='normal')
    cmd_y = Cpt(EpicsSignal, ':CMD:Y', kind='normal')
    cmd_z = Cpt(EpicsSignal, ':CMD:Z', kind='normal')
    cmd_rx = Cpt(EpicsSignal, ':CMD:RX', kind='normal')
    cmd_ry = Cpt(EpicsSignal, ':CMD:RY', kind='normal')
    cmd_rz = Cpt(EpicsSignal, ':CMD:RZ', kind='normal')



    """
    Stop
    """
    cmd_stop = Cpt(EpicsSignal, ':CMD:STOP', kind='normal')



    """
    Pose reachable?
    """
    cmd_reachable = Cpt(EpicsSignal, ':CMD:REACHABLE', kind='normal')
    reachable = Cpt(EpicsSignal, ':REACHABLE', kind='normal')



    """
    Positions - Readback
    """
    cmd_pos_rbv = Cpt(EpicsSignal, ':CMD:POS_RBV', kind='normal', doc='Readback current pose position')
    x_m = Cpt(EpicsSignal, ':X_M', kind='normal')
    y_m = Cpt(EpicsSignal, ':Y_M', kind='normal')
    z_m = Cpt(EpicsSignal, ':Z_M', kind='normal')
    x = Cpt(EpicsSignal, ':X', kind='normal')
    y = Cpt(EpicsSignal, ':Y', kind='normal')
    z = Cpt(EpicsSignal, ':Z', kind='normal')
    rx = Cpt(EpicsSignal, ':RX', kind='normal')
    ry = Cpt(EpicsSignal, ':RY', kind='normal')
    rz = Cpt(EpicsSignal, ':RZ', kind='normal')



    """
    Movement - Readback
    """
    moving = Cpt(EpicsSignal, ':MOVING', kind='normal', doc='Movement status')



    """
    Movement - Sync
    """
    cmd_sync = Cpt(EpicsSignal, ':CMD:SYNC', kind='normal')
    error_code = Cpt(EpicsSignal, ':ERROR_CODE', kind='normal')
    error_desc = Cpt(EpicsSignal, ':ERROR_DESC', kind='normal')



    """
    Pivot-point
    """
    cmd_pivot_rbv = Cpt(EpicsSignal, ':CMD:PIVOT_RBV', kind='normal', doc='Readback pivot point')
    cmd_set_pivot = Cpt(EpicsSignal, ':CMD:SET_PIVOT', kind='normal')
    cmd_sync_pivot = Cpt(EpicsSignal, ':CMD:SYNC_PIVOT', kind='normal')
    cmd_pivot_mode = Cpt(EpicsSignal, ':CMD:PIVOT_MODE', kind='normal')
    pivot_mode = Cpt(EpicsSignal, ':PIVOT_MODE', kind='normal', doc='Pivot mode')



    """
    Pivot positions
    """
    px_m = Cpt(EpicsSignal, ':PX_M', kind='normal')
    py_m = Cpt(EpicsSignal, ':PY_M', kind='normal')
    pz_m = Cpt(EpicsSignal, ':PZ_M', kind='normal')
    px = Cpt(EpicsSignal, ':PX', kind='normal')
    py = Cpt(EpicsSignal, ':PY', kind='normal')
    pz = Cpt(EpicsSignal, ':PZ', kind='normal')



    """
    Pivot request positions
    """
    cmd_px = Cpt(EpicsSignal, ':CMD:PX', kind='normal')
    cmd_py = Cpt(EpicsSignal, ':CMD:PY', kind='normal')
    cmd_pz = Cpt(EpicsSignal, ':CMD:PZ', kind='normal')



    """
    Miscellaneous
    """
    cmd_calibrate = Cpt(EpicsSignal, ':CMD:CALIBRATE', kind='normal')
    cmd_read_ver = Cpt(EpicsSignal, ':CMD:READ_VER', kind='normal')
    ver_sys = Cpt(EpicsSignal, ':VER:SYS', kind='normal')



    """
    Device Info
    """
    ver_sn  = Cpt(EpicsSignal, ':VER:SN', kind='normal')
    ver_product  = Cpt(EpicsSignal, ':VER:PRODUCT', kind='normal')
    ver_firmware = Cpt(EpicsSignal, ':VER:FIRMWARE', kind='normal')



    """
    Status
    """
    cmd_read_status = Cpt(EpicsSignal, ':CMD:READ_STATUS', kind='normal')
    status_temp = Cpt(EpicsSignal, ':STATUS:TEMP', kind='normal')
    status_load = Cpt(EpicsSignal, ':STATUS:LOAD', kind='normal')
    status_memory = Cpt(EpicsSignal, ':STATUS:MEMORY', kind='normal')
    status_net_bytes_in = Cpt(EpicsSignal, ':STATUS:NET_BYTES_IN', kind='normal')
    status_net_bytes_out = Cpt(EpicsSignal, ':STATUS:NET_BYTES_OUT', kind='normal')
    status_net = Cpt(EpicsSignal, ':STATUS:NET', kind='normal')
    status_status = Cpt(EpicsSignal, ':STATUS:STATUS', kind='normal')
    status_bootcnt = Cpt(EpicsSignal, ':STATUS:BOOTCNT', kind='normal')
    status_uptime = Cpt(EpicsSignal, ':STATUS:UPTIME', kind='normal')
    status_ip = Cpt(EpicsSignal, ':STATUS:IP', kind='normal')
    status_client_ip = Cpt(EpicsSignal, ':STATUS:CLIENT_IP', kind='normal')
    status_ser_status = Cpt(EpicsSignal, ':STATUS:SER_STATUS', kind='normal')
    status_ser_bytes_in = Cpt(EpicsSignal, ':STATUS:SER_BYTES_IN', kind='normal')
    status_ser_bytes_out = Cpt(EpicsSignal, ':STATUS:SER_BYTES_OUT', kind='normal')
    status_display = Cpt(EpicsSignal, ':STATUS:DISPLAY', kind='normal')
 


    """
    Sensor mode
    """
    cmd_sensor_mode = Cpt(EpicsSignal, ':CMD:SENSOR_MODE', kind='normal')
    sensor_mode = Cpt(EpicsSignal, ':SENSOR_MODE', kind='normal', doc='Sensor mode')



    """
    Maximum frequency 
    """
    cmd_freq = Cpt(EpicsSignal, ':CMD:FREQ', kind='normal')
    freq = Cpt(EpicsSignal, ':FREQ', kind='normal')



    """
    Maximum velocity
    """
    cmd_vel = Cpt(EpicsSignal, ':CMD:VEL', kind='normal')
    vel = Cpt(EpicsSignal, ':VEL', kind='normal')



    """
    Maximum acceleration
    """
    cmd_accel = Cpt(EpicsSignal, ':CMD:ACCEL', kind='normal')
    accel = Cpt(EpicsSignal, ':ACCEL', kind='normal')



    """
    Read and Set Poses, Pose 1-5:
    """
    pose_1_name = Cpt(EpicsSignal, ':POSE_1:NAME', kind='normal', doc='Pose 1 name input')
    pose_1_name_rbv = Cpt(EpicsSignal, ':POSE_1:NAME_RBV', kind='normal', doc='Pose 1 name readback')
    pose_1_x = Cpt(EpicsSignal, ':POSE_1:X', kind='normal', doc='Pose 1 X Position Data')
    pose_1_y = Cpt(EpicsSignal, ':POSE_1:Y', kind='normal', doc='Pose 1 Y Position Data')
    pose_1_z = Cpt(EpicsSignal, ':POSE_1:Z', kind='normal', doc='Pose 1 Z Position Data')
    pose_1_rx = Cpt(EpicsSignal, ':POSE_1:RX', kind='normal', doc='Pose 1 RX Position Data')
    pose_1_ry = Cpt(EpicsSignal, ':POSE_1:RY', kind='normal', doc='Pose 1 RY Position Data')
    pose_1_rz = Cpt(EpicsSignal, ':POSE_1:RZ', kind='normal', doc='Pose 1 RZ Position Data')
    pose_1_record = Cpt(EpicsSignal, ':POSE_1:RECORD', kind='normal', doc='Fanout for pose')
    pose_1_execute = Cpt(EpicsSignal, ':POSE_1:EXECUTE', kind='normal', doc='Enacts Pose 1 Positions')

    pose_2_name = Cpt(EpicsSignal, ':POSE_2:NAME', kind='normal', doc='Pose 2 name input')
    pose_2_name_rbv = Cpt(EpicsSignal, ':POSE_2:NAME_RBV', kind='normal', doc='Pose 2 name readback')
    pose_2_x = Cpt(EpicsSignal, ':POSE_2:X', kind='normal', doc='Pose 2 X Position Data')
    pose_2_y = Cpt(EpicsSignal, ':POSE_2:Y', kind='normal', doc='Pose 2 Y Position Data')
    pose_2_z = Cpt(EpicsSignal, ':POSE_2:Z', kind='normal', doc='Pose 2 Z Position Data')
    pose_2_rx = Cpt(EpicsSignal, ':POSE_2:RX', kind='normal', doc='Pose 2 RX Position Data')
    pose_2_ry = Cpt(EpicsSignal, ':POSE_2:RY', kind='normal', doc='Pose 2 RY Position Data')
    pose_2_rz = Cpt(EpicsSignal, ':POSE_2:RZ', kind='normal', doc='Pose 2 RZ Position Data')
    pose_2_record = Cpt(EpicsSignal, ':POSE_2:RECORD', kind='normal', doc='Fanout for pose')
    pose_2_execute = Cpt(EpicsSignal, ':POSE_2:EXECUTE', kind='normal', doc='Enacts Pose 2 Positions')

    pose_3_name = Cpt(EpicsSignal, ':POSE_3:NAME', kind='normal', doc='Pose 3 name input')
    pose_3_name_rbv = Cpt(EpicsSignal, ':POSE_3:NAME_RBV', kind='normal', doc='Pose 3 name readback')
    pose_3_x = Cpt(EpicsSignal, ':POSE_3:X', kind='normal', doc='Pose 3 X Position Data')
    pose_3_y = Cpt(EpicsSignal, ':POSE_3:Y', kind='normal', doc='Pose 3 Y Position Data')
    pose_3_z = Cpt(EpicsSignal, ':POSE_3:Z', kind='normal', doc='Pose 3 Z Position Data')
    pose_3_rx = Cpt(EpicsSignal, ':POSE_3:RX', kind='normal', doc='Pose 3 RX Position Data')
    pose_3_ry = Cpt(EpicsSignal, ':POSE_3:RY', kind='normal', doc='Pose 3 RY Position Data')
    pose_3_rz = Cpt(EpicsSignal, ':POSE_3:RZ', kind='normal', doc='Pose 3 RZ Position Data')
    pose_3_record = Cpt(EpicsSignal, ':POSE_3:RECORD', kind='normal', doc='Fanout for pose')
    pose_3_execute = Cpt(EpicsSignal, ':POSE_3:EXECUTE', kind='normal', doc='Enacts Pose 3 Positions')

    pose_4_name = Cpt(EpicsSignal, ':POSE_4:NAME', kind='normal', doc='Pose 4 name input')
    pose_4_name_rbv = Cpt(EpicsSignal, ':POSE_4:NAME_RBV', kind='normal', doc='Pose 4 name readback')
    pose_4_x = Cpt(EpicsSignal, ':POSE_4:X', kind='normal', doc='Pose 4 X Position Data')
    pose_4_y = Cpt(EpicsSignal, ':POSE_4:Y', kind='normal', doc='Pose 4 Y Position Data')
    pose_4_z = Cpt(EpicsSignal, ':POSE_4:Z', kind='normal', doc='Pose 4 Z Position Data')
    pose_4_rx = Cpt(EpicsSignal, ':POSE_4:RX', kind='normal', doc='Pose 4 RX Position Data')
    pose_4_ry = Cpt(EpicsSignal, ':POSE_4:RY', kind='normal', doc='Pose 4 RY Position Data')
    pose_4_rz = Cpt(EpicsSignal, ':POSE_4:RZ', kind='normal', doc='Pose 4 RZ Position Data')
    pose_4_record = Cpt(EpicsSignal, ':POSE_4:RECORD', kind='normal', doc='Fanout for pose')
    pose_4_execute = Cpt(EpicsSignal, ':POSE_4:EXECUTE', kind='normal', doc='Enacts Pose 4 Positions')

    pose_5_name = Cpt(EpicsSignal, ':POSE_5:NAME', kind='normal', doc='Pose 5 name input')
    pose_5_name_rbv = Cpt(EpicsSignal, ':POSE_5:NAME_RBV', kind='normal', doc='Pose 5 name readback')
    pose_5_x = Cpt(EpicsSignal, ':POSE_5:X', kind='normal', doc='Pose 5 X Position Data')
    pose_5_y = Cpt(EpicsSignal, ':POSE_5:Y', kind='normal', doc='Pose 5 Y Position Data')
    pose_5_z = Cpt(EpicsSignal, ':POSE_5:Z', kind='normal', doc='Pose 5 Z Position Data')
    pose_5_rx = Cpt(EpicsSignal, ':POSE_5:RX', kind='normal', doc='Pose 5 RX Position Data')
    pose_5_ry = Cpt(EpicsSignal, ':POSE_5:RY', kind='normal', doc='Pose 5 RY Position Data')
    pose_5_rz = Cpt(EpicsSignal, ':POSE_5:RZ', kind='normal', doc='Pose 5 RZ Position Data')
    pose_5_record = Cpt(EpicsSignal, ':POSE_5:RECORD', kind='normal', doc='Fanout for pose')
    pose_5_execute = Cpt(EpicsSignal, ':POSE_5:EXECUTE', kind='normal', doc='Enacts Pose 5 Positions')

