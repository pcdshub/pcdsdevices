import pytest
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import Signal

from pcdsdevices.device import InterfaceComponent as ICpt
from pcdsdevices.device import InterfaceDevice
from pcdsdevices.device import ObjectComponent as OCpt
from pcdsdevices.device import UnrelatedComponent as UCpt
from pcdsdevices.device import to_interface


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


class TwoSignal(InterfaceDevice):
    sig_one = ICpt(Signal)
    sig_two = ICpt(Signal)


class SomeDevice(Device):
    some = Cpt(Signal)
    where = Cpt(Signal)


def test_interface_basic():
    one = Signal(name='one')
    two = Signal(name='two')

    two_sig = TwoSignal('prefix', name='name', sig_one=one, sig_two=two)
    two_sig.sig_one.put(1)
    two_sig.sig_two.put(2)

    assert one.get() == 1
    assert two.get() == 2


def test_to_interface():
    SomeDeviceInterface = to_interface(SomeDevice)
    some = Signal(name='some')
    where = Signal(name='where')

    sdi = SomeDeviceInterface('', name='sdi', some=some, where=where)
    sd = SomeDevice('', name='sd')

    sdi.some.put(1)
    sdi.where.put(2)
    sd.some.put(3)
    sd.where.put(4)

    assert some.get() == 1
    assert where.get() == 2
