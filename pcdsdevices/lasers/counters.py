"""
Module for counters such as frequency counters and time interval counters.
"""

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

from pcdsdevices.interface import BaseInterface
from pcdsdevices.variety import set_metadata


class Agilent53210A(BaseInterface, Device):
    """
    Agililent 53210A frequency counter class.

    For use with IOC ioc/common/agilent5322.
    """
    protocol = Cpt(EpicsSignal, ':PROTOCOL_RBV', write_pv=':PROTOCOL',
                   kind='omitted')

    freq_rbck = Cpt(EpicsSignalRO, ':FREQ_RBCK', kind='normal')
    freq_rbck_raw = Cpt(EpicsSignalRO, ':FREQ_RBCK_RAW', kind='omitted')

    auto_level = Cpt(EpicsSignal, ':GET_AUTO_LEVEL',
                     write_pv=':SET_AUTO_LEVEL', kind='config')

    coupling = Cpt(EpicsSignal, ':GET_COUPLING', write_pv=':SET_COUPLING',
                   kind='config')

    impedance = Cpt(EpicsSignal, ':GET_IMPEDANCE', write_pv=':SET_IMPEDANCE',
                    kind='config')

    noise_rej = Cpt(EpicsSignal, ':GET_NOISE_REJ', write_pv=':SET_NOISE_REJ',
                    kind='config')

    trig_level = Cpt(EpicsSignal, ':GET_TRIG_LEVEL',
                     write_pv=':SET_TRIG_LEVEL', kind='config')

    trig_percent = Cpt(EpicsSignal, ':GET_TRIG_PERCENT',
                       write_pv=':SET_TRIG_PERCENT', kind='config')

    identity = Cpt(EpicsSignalRO, ':IDENTITY', kind='omitted')

    reset = Cpt(EpicsSignal, ':RESET', kind='config')
    set_metadata(reset, dict(variety='command-proc', value=1))
