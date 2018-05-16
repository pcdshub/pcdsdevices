import logging
import pytest

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.positioner import SoftPositioner

from pcdsdevices.pseudopos import SyncAxes

logger = logging.getLogger(__name__)


AXES = ('one', 'two', 'three', 'four', 'five')


@pytest.fixture(scope='function')
def five_axes():
    kwargs = dict(name='sync', egu='five')
    for ax in AXES:
        kwargs[ax] = Cpt(SoftPositioner)
    return SyncAxes(**kwargs)


def test_sync_passthrough(five_axes):
    logger.debug('test_sync_passthrough')
    assert five_axes.name == 'sync'
    assert five_axes.egu == 'five'


def test_sync_move(five_axes):
    logger.debug('test_sync_move')
    five_axes.move(5)
    for ax in AXES:
        axis = getattr(five_axes, ax)
        assert axis.position == 5
    assert five_axes.position == 5


def test_sync_mean(five_axes):
    logger.debug('test_sync_mean')
    for i, ax in enumerate(AXES):
        axis = getattr(five_axes, ax)
        axis.move(i)
    assert five_axes.position == np.mean(range(len(AXES)))
