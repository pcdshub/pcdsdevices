import logging

import pytest
from ophyd.sim import make_fake_device

from ..jet import BeckhoffJet, Injector, InjectorWithFine

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_jet_init():
    logger.debug('test_jet_init')
    FakeJet = make_fake_device(Injector)
    FakeJet(name='test', x_prefix='X', y_prefix='Y', z_prefix='Z')
    FakeJet = make_fake_device(InjectorWithFine)
    FakeJet(name='test', x_prefix='X', y_prefix='Y', z_prefix='Z',
            fine_x_prefix='x', fine_y_prefix='y', fine_z_prefix='z')
    FakeJet = make_fake_device(BeckhoffJet)
    FakeJet('TST', name='test')


@pytest.mark.timeout(5)
def test_jet_disconnected():
    logger.debug('test_jet_disconnected')
    Injector(name='test', x_prefix='X', y_prefix='Y', z_prefix='Z')
    InjectorWithFine(name='test', x_prefix='X', y_prefix='Y', z_prefix='Z',
                     fine_x_prefix='x', fine_y_prefix='y', fine_z_prefix='z')
    BeckhoffJet('TST', name='test')
