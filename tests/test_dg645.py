import pytest
from ophyd.sim import make_fake_device

#from pcdsdevices.dg645 import DG645
from dg645 import DG645

@pytest.fixture(scope='function')
def fake_dg():
    FakeDG = make_fake_device(DG645)
    DG = FakeDG("TST:DDG", name='test_DG')
    # set delay - device handles this as SI
    DG.chAB.delay(0.0)
    #DG.chAB.delay_channel.delay_pv.put('A + 0.000000e0')
    # set pulse width - device handles this as SI
    DG.chAB.width_channel.delay_pv.put('A + 1.00000e-05')
    # set pulse amplitude
    DG.chAB.amplitude(1.0)
    # set polarity
    DG.chAB.polarity('POS')
    # set trigger source
    DG.chAB.trig_source('Ext ^edge')
    # set trigger inhibit
    DG.chAB.trig_inhib('OFF')
    return DG
    
def test_delays(fake_dg):
    DG = fake_dg
    # Max delay
    DG.chAB.delay(1.0)
    assert DG.chAB.delay() == 5.0

