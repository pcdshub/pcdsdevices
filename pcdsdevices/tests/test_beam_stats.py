import logging

import pytest
from ophyd.sim import make_fake_device

from ..beam_stats import LCLS, BeamStats

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
