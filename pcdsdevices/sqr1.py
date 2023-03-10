"""
Ophyd class for square-one motion system
"""

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

import time
import logging

logger = logging.getLogger(__name__)

class SQR1(Device):
    motor_move = Cpt(EpicsSignal, ':MOV', kind='normal')
    motor_stop = Cpt(EpicsSignal, ':KILL', kind='normal')
    emergency_stop = Cpt(EpicsSignal, ':ESTOP', kind='normal')
    status = Cpt(EpicsSignalRO, ':STAT', kind='normal')
    local_control = Cpt(EpicsSignal, ':LOC', kind='normal')
    reset_position = Cpt(EpicsSignal, ':POS_RESET', kind='normal')
    is_target_out_of_range = Cpt(EpicsSignalRO, ':TARGET_ERR', kind='normal')

    x_setpoint=Cpt(EpicsSignal, ':TARGET:X',     kind='normal')
    x_readback=Cpt(EpicsSignal, ':TARGET:X:RBV', kind='normal')
    x_llm=Cpt(EpicsSignalRO,    ':TARGET:X:LLM', kind='normal')
    x_hlm=Cpt(EpicsSignalRO,    ':TARGET:X:HLM', kind='normal')

    y_setpoint=Cpt(EpicsSignal, ':TARGET:Y',     kind='normal')
    y_readback=Cpt(EpicsSignal, ':TARGET:Y:RBV', kind='normal')
    y_llm=Cpt(EpicsSignalRO,    ':TARGET:Y:LLM', kind='normal')
    y_hlm=Cpt(EpicsSignalRO,    ':TARGET:Y:HLM', kind='normal')

    z_setpoint=Cpt(EpicsSignal, ':TARGET:Z',     kind='normal')
    z_readback=Cpt(EpicsSignal, ':TARGET:Z:RBV', kind='normal')
    z_llm=Cpt(EpicsSignalRO,    ':TARGET:Z:LLM', kind='normal')
    z_hlm=Cpt(EpicsSignalRO,    ':TARGET:Z:HLM', kind='normal')

    rx_setpoint=Cpt(EpicsSignal, ':TARGET:rX',     kind='normal')
    rx_readback=Cpt(EpicsSignal, ':TARGET:rX:RBV', kind='normal')
    rx_llm=Cpt(EpicsSignalRO,    ':TARGET:rX:LLM', kind='normal')
    rx_hlm=Cpt(EpicsSignalRO,    ':TARGET:rX:HLM', kind='normal')

    ry_setpoint=Cpt(EpicsSignal, ':TARGET:rY',     kind='normal')
    ry_readback=Cpt(EpicsSignal, ':TARGET:rY:RBV', kind='normal')
    ry_llm=Cpt(EpicsSignalRO,    ':TARGET:rY:LLM', kind='normal')
    ry_hlm=Cpt(EpicsSignalRO,    ':TARGET:rY:HLM', kind='normal')

    rz_setpoint=Cpt(EpicsSignal, ':TARGET:rZ',     kind='normal')
    rz_readback=Cpt(EpicsSignal, ':TARGET:rZ:RBV', kind='normal')
    rz_llm=Cpt(EpicsSignalRO,    ':TARGET:rZ:LLM', kind='normal')
    rz_hlm=Cpt(EpicsSignalRO,    ':TARGET:rZ:HLM', kind='normal')

    def move(self, *, x=None, y=None, z=None, rx=None, ry=None, rz=None, wait_time=0):
        x_readback=self.x_readback.get()
        y_readback=self.y_readback.get()
        z_readback=self.z_readback.get()
        rx_readback=self.rx_readback.get()
        ry_readback=self.ry_readback.get()
        rz_readback=self.rz_readback.get()

        x=x_readback if x is None else x
        y=y_readback if y is None else y 
        z=z_readback if z is None else z 
        rx=rx_readback if rx is None else rx
        ry=ry_readback if ry is None else ry
        rz=rz_readback if rz is None else rz


        x_llm=self.x_llm.get()
        x_hlm=self.x_hlm.get()
        y_llm=self.y_llm.get()
        y_hlm=self.y_hlm.get()
        z_llm=self.z_llm.get()
        z_hlm=self.z_hlm.get()
        rx_llm=self.rx_llm.get()
        rx_hlm=self.rx_hlm.get()
        ry_llm=self.ry_llm.get()
        ry_hlm=self.ry_hlm.get()
        rz_llm=self.rz_llm.get()
        rz_hlm=self.rz_hlm.get()

        x   = x_readback  if x  > x_hlm  or x  < x_llm  else x
        y   = y_readback  if y  > y_hlm  or y  < y_llm  else y
        z   = z_readback  if z  > z_hlm  or z  < z_llm  else z
        rx  = rx_readback if rx > rx_hlm or rx < rx_llm else rx
        ry  = ry_readback if ry > ry_hlm or ry < ry_llm else ry
        rz  = rz_readback if rz > rz_hlm or rz < rz_llm else rz

        self.x_setpoint.put(x)
        self.y_setpoint.put(y)
        self.z_setpoint.put(z)
        self.rx_setpoint.put(rx)
        self.ry_setpoint.put(ry)
        self.rz_setpoint.put(rz)

        logger.info(f"move command: x:{x} | y:{y} | z:{z} | rx:{rx} | ry:{ry} |rz:{rz}")

        self.motor_move.put(1)

        # since there is no motion completion status pv, we are relying on sleep time
        time.sleep(wait_time)