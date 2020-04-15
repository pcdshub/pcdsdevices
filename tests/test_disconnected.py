import pytest
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal


class Disconnected(Device):
    sig01 = Cpt(EpicsSignal, '01')
    sig02 = Cpt(EpicsSignal, '02')
    sig03 = Cpt(EpicsSignal, '03')
    sig04 = Cpt(EpicsSignal, '04')
    sig05 = Cpt(EpicsSignal, '05')
    sig06 = Cpt(EpicsSignal, '06')
    sig07 = Cpt(EpicsSignal, '07')
    sig08 = Cpt(EpicsSignal, '08')
    sig09 = Cpt(EpicsSignal, '09')
    sig10 = Cpt(EpicsSignal, '10')
    sig11 = Cpt(EpicsSignal, '11')
    sig12 = Cpt(EpicsSignal, '12')
    sig13 = Cpt(EpicsSignal, '13')
    sig14 = Cpt(EpicsSignal, '14')
    sig15 = Cpt(EpicsSignal, '15')
    sig16 = Cpt(EpicsSignal, '16')
    sig17 = Cpt(EpicsSignal, '17')
    sig18 = Cpt(EpicsSignal, '18')
    sig19 = Cpt(EpicsSignal, '19')
    sig20 = Cpt(EpicsSignal, '20')


@pytest.mark.timeout(5)
def test_instantiate_disconnected():
    """Check if environment handles disconnected devices gracefully"""
    Disconnected('NO:CONN:', name='no_conn')
