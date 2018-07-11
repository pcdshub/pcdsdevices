import logging
import pytest

from ophyd.device import Component as Cpt
from ophyd.positioner import SoftPositioner

from pcdsdevices.pseudopos import SyncAxesBase

logger = logging.getLogger(__name__)


class FiveSyncSoftPositioner(SyncAxesBase):
    one = Cpt(SoftPositioner, init_pos=0)
    two = Cpt(SoftPositioner, init_pos=0)
    three = Cpt(SoftPositioner, init_pos=0)
    four = Cpt(SoftPositioner, init_pos=0)
    five = Cpt(SoftPositioner, init_pos=0)


@pytest.fixture(scope='function')
def five_axes():
    return FiveSyncSoftPositioner(name='sync', egu='five')


def test_sync_passthrough(five_axes):
    logger.debug('test_sync_passthrough')
    assert five_axes.name == 'sync'
    assert five_axes.egu == 'five'


def test_sync_basic(five_axes):
    logger.debug('test_sync_basic')
    five_axes.move(5)
    for pos in five_axes.real_position:
        assert pos == 5
    assert five_axes.position == 5


def test_sync_offset(five_axes):
    logger.debug('test_sync_offset')
    five_axes.one.move(1)
    five_axes.two.move(2)
    five_axes.three.move(3)
    five_axes.four.move(4)
    five_axes.five.move(5)
    five_axes.save_offsets()
    assert five_axes.position == 1
    five_axes.move(10)
    assert five_axes.one.position == 10
    assert five_axes.two.position == 11
    assert five_axes.three.position == 12
    assert five_axes.four.position == 13
    assert five_axes.five.position == 14
    five_axes.save_offsets(two=10)
    five_axes.move(11)
    assert five_axes.one.position == 11
    assert five_axes.two.position == 21
    assert five_axes.three.position == 13
    five_axes._mode = max
    five_axes.save_offsets()
    assert five_axes.position == 21
