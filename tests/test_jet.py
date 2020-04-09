import logging

import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.jet import BeckhoffJet

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_jet_init():
    logger.debug('test_jet_init')
    FakeVH = make_fake_device(BeckhoffJet)
    FakeVH('TST', name='test')


@pytest.mark.timeout(5)
def test_jet_disconnected():
    logger.debug('test_jet_disconnected')
    BeckhoffJet('TST', name='test')
