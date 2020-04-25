import logging

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.jet import BeckhoffJet, Injector

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_jet_init():
    logger.debug('test_jet_init')
    FakeJet = make_fake_device(Injector)
    FakeJet('TST', name='test', coarseX_prefix='X', coarseY_prefix='Y',
            coarseZ_prefix='Z', fineX_prefix='x', fineY_prefix='y',
            fineZ_prefix='z')
    FakeJet = make_fake_device(BeckhoffJet)
    FakeJet('TST', name='test')


@pytest.mark.timeout(5)
def test_jet_disconnected():
    logger.debug('test_jet_disconnected')
    Injector('TST', name='test', coarseX_prefix='X', coarseY_prefix='Y',
             coarseZ_prefix='Z', fineX_prefix='x', fineY_prefix='y',
             fineZ_prefix='z')
    BeckhoffJet('TST', name='test')
