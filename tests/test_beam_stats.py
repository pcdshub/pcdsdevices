import logging

import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.beam_stats import BeamStats

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

    assert stats.mj_avg.value == sum(range(10))/10

    stats.configure(dict(mj_buffersize=20))
    cfg = stats.read_configuration()

    assert cfg['beam_stats_mj_buffersize']['value'] == 20


@pytest.mark.timeout(5)
def test_beam_stats_disconnected():
    BeamStats()
