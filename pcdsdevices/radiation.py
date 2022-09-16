"""
Radiation Sesnsor Classes.

This Module contains all the classes relating to Radiation instrumentation
"""
from ophyd import Component as Cpt
from ophyd import EpicsSignalRO
from ophyd.device import Device


class HPI6030(Device):
    """class for reading out 6030 sensor data"""
    dose_rate = Cpt(EpicsSignalRO, ':DOSE_RATE', kind='hinted')

    trip_alarm_a1 = Cpt(EpicsSignalRO, ':TRIP_A1')
    trip_alarm_a2 = Cpt(EpicsSignalRO, ':TRIP_A2')
    trip_alarm_a3 = Cpt(EpicsSignalRO, ':TRIP_A3')

    fail_time = Cpt(EpicsSignalRO, ':FAIL_TIME')
