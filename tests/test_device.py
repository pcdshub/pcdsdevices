from ophyd.signal import Signal

from pcdsdevices.component import InterfaceComponent as ICpt
from pcdsdevices.device import InterfaceDevice


class TwoSignal(InterfaceDevice):
    sig_one = ICpt(Signal)
    sig_two = ICpt(Signal)


def test_interface_basic():
    one = Signal(name='one')
    two = Signal(name='two')

    two_sig = TwoSignal('prefix', name='name', sig_one=one, sig_two=two)
    two_sig.sig_one.put(1)
    two_sig.sig_two.put(2)

    assert one.get() == 1
    assert two.get() == 2
