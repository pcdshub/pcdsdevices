from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import Signal

from pcdsdevices.component import InterfaceComponent as ICpt
from pcdsdevices.device import InterfaceDevice, to_interface


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
