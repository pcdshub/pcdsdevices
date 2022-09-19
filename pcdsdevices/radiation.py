"""
Radiation Sensor Classes.

This Module contains all the classes relating to Radiation instrumentation
"""
from ophyd import Component as Cpt
from ophyd import EpicsSignalRO
from ophyd.device import Device


class HPI6030(Device):
    """
    The Human Physics Instrument 6030 radiation sensor is controlled
    by the HPI 6012 which sends readout data over RS232.

    """
    dose_rate = Cpt(EpicsSignalRO, ':DOSE_RATE', kind='hinted')

    trip_alarm_a1 = Cpt(EpicsSignalRO, ':TRIP_A1')
    trip_alarm_a2 = Cpt(EpicsSignalRO, ':TRIP_A2')
    trip_alarm_a3 = Cpt(EpicsSignalRO, ':TRIP_A3')

    fail_time = Cpt(EpicsSignalRO, ':FAIL_TIME')
