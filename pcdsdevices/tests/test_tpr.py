import pytest
from ophyd.sim import make_fake_device

from ..tpr import TimingMode, TprTrigger


@pytest.fixture(scope='function')
def fake_trigger():
    cls = make_fake_device(TprTrigger)
    return cls('TST:TPR', channel=10, timing_mode=TimingMode.LCLS2, name='trig_a')


def test_enable(fake_trigger):
    fake_trigger.enable()
    assert fake_trigger.enable_ch_cmd.get() == 1
    assert fake_trigger.enable_trg_cmd.get() == 1
    fake_trigger.disable()
    assert fake_trigger.enable_ch_cmd.get() == 0
    assert fake_trigger.enable_trg_cmd.get() == 0


@pytest.mark.timeout(5)
def test_disconnected_trigger():
    TprTrigger('TST', channel=1, timing_mode=TimingMode.LCLS1, name='test')
