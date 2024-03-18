"""
Module for Keithely classes.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from .interface import BaseInterface


class K6514(BaseInterface, Device):
    """
    Keithley 6514 electrometer.

    Used by GMD.
    """
    tab_component_names = True

    avg_enable = Cpt(EpicsSignal, ':AvgEnable', kind='normal', doc='Enable/disable the average function')
    avg_count = Cpt(EpicsSignal, ':GetAvgCount', write_pv='PutAvgCount', kind='normal', doc='Get the averaging factor')
    avg_mode = Cpt(EpicsSignal, ':PutAvgType', string=True, kind='normal', doc='Select filter control: Moving or Repeated')
    auto_range = Cpt(EpicsSignal, ':PutAutoRange', kind='normal', doc='Enable/disable autorange')
    current_range = Cpt(EpicsSignal, ':SelectCurrentRange', string=True, kind='normal', doc='Set range in amps')
    damping = Cpt(EpicsSignal, ':PutDamping', string=True, kind='normal', doc='Enable/disable current damping')
    integration_time = Cpt(EpicsSignal, ':GetIntCycles', write_pv=':PutIntCycles', kind='hinted', doc='Set integration time')
    measurement_function = Cpt(EpicsSignal, ':PutFunction', string=True, kind='hinted', doc='Select function - Voltage, Current, Resistance, or Charge')
    reading_rate = Cpt(EpicsSignal, ':Reading.SCAN', string=True, kind='normal', doc='Reading scan rate/type')
    reading = Cpt(EpicsSignalRO, ':Reading', kind='hinted', doc='Trigger and return a new measurement')
    zero_correct = Cpt(EpicsSignal, ':ZeroCorrect', kind='normal', doc='Run zero-correct')


class K2700(BaseInterface, Device):
    """
    Keithley 2700 digital multimeter.

    Currently supports reading voltage and current, direct and
    alternating, but can be extended to measure other quantities
    (resistance, temperature), have configurable range and integration
    time, and allow for remote control of a K2700.
    """
    idn = Cpt(EpicsSignalRO, ":Identity", kind="normal",
              doc='Identity (name) of this device')
    reading = Cpt(EpicsSignalRO, ":Reading", kind="normal",
                  doc='Trigger and return a new measurement')
    dcv_range = Cpt(EpicsSignalRO, ":GetDCV", kind="normal",
                    doc='DC voltage range')
    acv_range = Cpt(EpicsSignalRO, ":GetACV", kind="normal",
                    doc='AC voltage range')
    dci_range = Cpt(EpicsSignalRO, ":GetDCI", kind="normal",
                    doc='DC current range')
    aci_range = Cpt(EpicsSignalRO, ":GetACI", kind="normal",
                    doc='AC current range')


class IM3L0_K2700(K2700):
    """
    One-off subclass of K2700 to use a pydm screen specific to this device.

    Identical to K2700 class, but uses a pydm screen for this particular device
    in place of the default detailed screen. To be used in conjunction with
    IM3L0 as this Keithley is added to that imager for detailed power readouts.
    """
    pass
