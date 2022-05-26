import logging

import pytest
from ophyd.sim import make_fake_device

from ..beam_stats import (LCLS, BeamEnergyRequest, BeamEnergyRequestACRWait,
                          BeamEnergyRequestNoWait, BeamStats,
                          FakeBeamEnergyRequestACRWait,
                          FakeBeamEnergyRequestNoWait)

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_beam_stats():
    FakeStats = make_fake_device(BeamStats)
    stats = FakeStats()
    stats.mj.sim_put(-1)
    return stats


def test_beam_stats(fake_beam_stats):
    logger.debug('test_beam_stats')
    stats = fake_beam_stats
    stats.read()
    stats.hints


def test_beam_stats_avg(fake_beam_stats):
    logger.debug('test_beam_stats_avg')
    stats = fake_beam_stats

    assert stats.mj_buffersize.get() == 120

    stats.mj_buffersize.put(10)

    for i in range(10):
        stats.mj.sim_put(i)

    assert stats.mj_avg.get() == sum(range(10))/10

    stats.configure(dict(mj_buffersize=20))
    cfg = stats.read_configuration()

    assert cfg['beam_stats_mj_buffersize']['value'] == 20


@pytest.mark.timeout(5)
def test_beam_stats_disconnected():
    BeamStats()


@pytest.fixture(scope='function')
def fake_lcls():
    FakeLcls = make_fake_device(LCLS)
    lcls = FakeLcls()
    lcls.bykik_period.sim_put(200)
    return lcls


def test_lcls(fake_lcls):
    lcls = fake_lcls
    lcls.read()
    lcls.hints


def test_bykik_status(fake_lcls):
    lcls = fake_lcls
    lcls.bykik_abort.put('Enable')
    assert lcls.bykik_status() == 'Enable'
    lcls.bykik_abort.put('Disable')
    assert lcls.bykik_status() == 'Disable'


def test_bykik_disable(fake_lcls):
    lcls = fake_lcls
    lcls.bykik_disable()
    assert lcls.bykik_status() == 'Disable'


def test_bykik_enable(fake_lcls):
    lcls = fake_lcls
    lcls.bykik_enable()
    assert lcls.bykik_status() == 'Enable'


def test_get_set_period(fake_lcls):
    lcls = fake_lcls
    assert lcls.bykik_get_period() == 200
    lcls.bykik_set_period(100)
    assert lcls.bykik_get_period() == 100


@pytest.mark.timeout(5)
def test_beam_energy_request_args():
    # Defaults for xpp and tmo
    xpp_request = BeamEnergyRequest(
        'XPP',
        name='xpp_request',
        skip_small_moves=True,
    )
    assert xpp_request.setpoint.pvname == 'XPP:USER:MCC:EPHOT:SET1'
    tmo_request = BeamEnergyRequest('TMO', name='tmo_request', atol=4)
    assert tmo_request.setpoint.pvname == 'TMO:USER:MCC:EPHOTK:SET1'
    # Future TXI and multi-bunch specific options
    tst_k1_request = BeamEnergyRequest(
        'TST',
        name='tst_k1_request',
        line='k',
        bunch=1,
    )
    assert tst_k1_request.setpoint.pvname == 'TST:USER:MCC:EPHOTK:SET1'
    tst_l2_request = BeamEnergyRequest(
        'TST',
        name='tst_l2_request',
        line='L',
        bunch=2,
    )
    assert tst_l2_request.setpoint.pvname == 'TST:USER:MCC:EPHOT:SET2'
    # let's test the class splitting here too
    for obj in (
        xpp_request,
        tmo_request,
        tst_k1_request,
        tst_l2_request,
    ):
        assert isinstance(obj, BeamEnergyRequestNoWait)
        assert isinstance(obj, BeamEnergyRequest)
    # including a done PV
    tst_l1_request = BeamEnergyRequest(
        'TST',
        name='tst_l2_request',
        acr_status_suffix='TSTSUFFIX',
    )
    assert isinstance(tst_l1_request, BeamEnergyRequest)
    assert isinstance(tst_l1_request, BeamEnergyRequestACRWait)
    assert 'TSTSUFFIX' in tst_l1_request.done.pvname


@pytest.mark.timeout(5)
def test_beam_energy_request_behavior():
    FakeCls = make_fake_device(BeamEnergyRequest)

    # No wait variant: reports done immediately, skips moves smaller than atol
    nowait = FakeCls('TST', name='nowait', skip_small_moves=True, atol=0.9)
    assert isinstance(nowait, FakeBeamEnergyRequestNoWait)
    nowait.setpoint.put(0)
    assert nowait.position == 0
    nowait.move(0.1, timeout=0.1)
    assert nowait.position == 0
    nowait.move(1, timeout=0.1)
    assert nowait.position == 1

    # Wait variant: acr needs to put 0 to when moving and 1 back when done
    acrwait = FakeCls('TST', name='acrwait', acr_status_suffix='WAITER')
    assert isinstance(acrwait, FakeBeamEnergyRequestACRWait)
    acrwait.done.sim_put(1)
    st = acrwait.move(1, wait=False)
    try:
        st.wait(timeout=0.1)
    except Exception:
        ...
    assert not st.done
    acrwait.done.sim_put(0)
    try:
        st.wait(timeout=0.1)
    except Exception:
        ...
    assert not st.done
    acrwait.done.sim_put(1)
    try:
        st.wait(timeout=1)
    except Exception:
        ...
    assert st.done
