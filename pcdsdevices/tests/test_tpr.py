import pytest
from ophyd.sim import make_fake_device

from ..tpr import TPR_TAP_NS, TPR_TICK_NS, TimingMode, TprTrigger


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


def put_equals_setpoint(mds, setpoint, ns_time):
    status = mds.put(ns_time)
    status.wait()
    return setpoint.get() == ns_time


def mds_get(mds, tick_signal, tap_signal, num_ticks, num_taps):
    tick_signal.put(num_ticks)
    tap_signal.put(num_taps)
    return mds.get() == (TPR_TICK_NS * num_ticks + TPR_TAP_NS * num_taps)


@pytest.mark.timeout(5)
def test_ns_delay(fake_trigger):
    assert put_equals_setpoint(fake_trigger.ns_delay, fake_trigger.delay_setpoint, 100)
    assert mds_get(fake_trigger.ns_delay, fake_trigger.delay_ticks, fake_trigger.delay_taps, 0, 7)


@pytest.mark.timeout(5)
def test_width(fake_trigger):
    assert put_equals_setpoint(fake_trigger.width, fake_trigger.width_setpoint, 100)
    assert fake_trigger.width.get() == fake_trigger.width_ticks.get() * TPR_TICK_NS


def test_motor(fake_trigger):
    assert mds_get(fake_trigger.ns_delay_scan.readback, fake_trigger.ns_delay_scan.delay_ticks,
                   fake_trigger.ns_delay_scan.delay_taps, 3, 3)
