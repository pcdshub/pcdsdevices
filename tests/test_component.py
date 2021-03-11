import pytest
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import Signal

from pcdsdevices.component import ObjectComponent as OCpt
from pcdsdevices.component import UnrelatedComponent as UCpt


class Basic(Device):
    apple = UCpt(Device)
    sauce = UCpt(Device)
    empty = Cpt(Device, ':EMPTY')

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class Complex(Device):
    one = UCpt(Basic)
    two = UCpt(Basic)
    tomayto = Cpt(Device, ':TOMAHTO')

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


def test_basic_class_good():
    obj = Basic('GLASS', name='jar', apple_prefix='APPLE',
                sauce_prefix='SAUCE')
    assert obj.prefix == 'GLASS'
    assert obj.apple.prefix == 'APPLE'
    assert obj.sauce.prefix == 'SAUCE'
    assert obj.empty.prefix == 'GLASS:EMPTY'


def test_basic_class_bad():
    with pytest.raises(ValueError):
        Basic('GLASS', name='jar', apple_prefix='APPLE')


def test_complex_class():
    obj = Complex('APPT', name='apt',
                  one_prefix='UNO',
                  one_apple_prefix='APPLE:01',
                  one_sauce_prefix='SAUCE:01',
                  two_prefix='DOS',
                  two_apple_prefix='APPLE:02',
                  two_sauce_prefix='SAUCE:02')

    assert obj.prefix == 'APPT'
    assert obj.one.prefix == 'UNO'
    assert obj.one.apple.prefix == 'APPLE:01'
    assert obj.one.sauce.prefix == 'SAUCE:01'
    assert obj.one.empty.prefix == 'UNO:EMPTY'
    assert obj.two.prefix == 'DOS'
    assert obj.two.apple.prefix == 'APPLE:02'
    assert obj.two.sauce.prefix == 'SAUCE:02'
    assert obj.two.empty.prefix == 'DOS:EMPTY'
    assert obj.tomayto.prefix == 'APPT:TOMAHTO'


def test_ocpt():
    sig_one = Signal(name='one')
    sig_two = Signal(name='two')

    class ObjectDevice(Device):
        one = OCpt(sig_one)
        two = OCpt(sig_two)

    obj = ObjectDevice('prefix', name='name')
    assert 'one' in obj.component_names
    obj.one.put(5)
    assert sig_one.get() == 5
    obj.two.put(3)
    assert sig_two.get() == 3
