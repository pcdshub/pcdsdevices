import logging
import os
import os.path
import sys
from unittest.mock import Mock

import numpy as np
import pytest
from ophyd.sim import make_fake_device

from ..lens import XFLS, LensStack, LensStackBase, Prefocus, SimLensStack

logger = logging.getLogger(__name__)

sample_lens_file = os.path.dirname(__file__) + '/test_lens_sets/test'
sample_lens_set = [2, 200e-6, 4, 500e-6]
sample_E = 8


@pytest.fixture(scope='function')
def fake_xfls():
    FakeXFLS = make_fake_device(XFLS)
    xfls = FakeXFLS('TST:XFLS', name='lens')
    xfls.state.sim_put(4)
    xfls.state.sim_set_enum_strs(('Unknown', 'LENS1', 'LENS2', 'LENS3', 'OUT'))
    return xfls


def test_xfls_states(fake_xfls):
    logger.debug('test_xfls_states')
    xfls = fake_xfls
    # Remove
    xfls.state.put(4)
    assert xfls.removed
    assert not xfls.inserted
    # Insert
    xfls.state.put(3)
    assert not xfls.removed
    assert xfls.inserted
    # Unknown
    xfls.state.put(0)
    assert not xfls.removed
    assert not xfls.inserted


def test_xfls_motion(fake_xfls):
    logger.debug('test_xfls_motion')
    xfls = fake_xfls
    xfls.remove()
    assert xfls.state.get() == 4


def test_xfls_subscriptions(fake_xfls):
    logger.debug('test_xfls_subscriptions')
    xfls = fake_xfls
    # Subscribe a pseudo callback
    cb = Mock()
    xfls.subscribe(cb, event_type=xfls.SUB_STATE, run=False)
    # Change readback state
    xfls.state.put(4)
    assert cb.called


@pytest.fixture(scope='function')
def fake_prefocus():
    FakePrefocus = make_fake_device(Prefocus)
    prefocus = FakePrefocus('TST:PFLS', name='prefocus')
    prefocus.state.sim_set_enum_strs(('Unknown', 'OUT', 'LENS1', 'LENS2',
                                      'LENS3'))
    prefocus.state.sim_put(1)
    return prefocus


def test_prefocus_states(fake_prefocus):
    logger.debug('test_prefocus_states')
    prefocus = fake_prefocus
    # Remove
    prefocus.state.put(1)
    assert prefocus.removed
    assert not prefocus.inserted
    # Insert
    prefocus.state.put(2)
    assert not prefocus.removed
    assert prefocus.inserted
    # Unknown
    prefocus.state.put(0)
    assert not prefocus.removed
    assert not prefocus.inserted


def test_prefocus_motion(fake_prefocus):
    logger.debug('test_prefocus_motion')
    prefocus = fake_prefocus
    prefocus.insert()
    assert prefocus.state.get() == 2
    prefocus.remove()
    assert prefocus.state.get() == 1


def test_prefocus_subscriptions(fake_prefocus):
    logger.debug('test_prefocus_subscriptions')
    prefocus = fake_prefocus
    # Subscribe a pseudo callback
    cb = Mock()
    prefocus.subscribe(cb, event_type=prefocus.SUB_STATE, run=False)
    # Change readback state
    prefocus.state.put(1)
    assert cb.called


@pytest.fixture(scope='function')
def fake_lensstack(fake_att):
    fake_lensstack = SimLensStack(name='test', x_prefix='x_motor',
                                  y_prefix='y_motor', z_prefix='z_motor',
                                  path=sample_lens_file,
                                  E=sample_E,
                                  z_offset=.01, z_dir=1, att_obj=fake_att,
                                  lcls_obj=.01, mono_obj=.01)
    return fake_lensstack


def test_lensstack_beamsize(monkeypatch, fake_lensstack):
    logger.debug('test_lensstackbeamsize')
    lensstack = fake_lensstack
    lensstack.beam_size.move(500e-6)

    def mocktweak(self):
        lensstack.x.move(lensstack.x.position+1)
        lensstack.y.move(lensstack.y.position+1)
    monkeypatch.setattr(LensStackBase, 'tweak', mocktweak)
    lensstack.align(0)
    assert np.isclose(lensstack.beam_size.position, 500e-6, rtol=0.1, atol=0)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Fails on Windows, presets needed and not supported.",
    )
def test_lensstack_align(presets, monkeypatch, fake_lensstack):
    logger.debug('test_lensstack_align')

    def mocktweak(self):
        lens.x.move(lens.x.position+1)
        lens.y.move(lens.y.position+1)
    lens = fake_lensstack
    monkeypatch.setattr(LensStackBase, 'tweak', mocktweak)
    lens.align(0)
    assert lens.x.position == 1.5
    assert lens.y.position == 1.5
    assert lens.z.position == 0


def test_move(fake_lensstack):
    logger.debug('test_move')
    lensstack = fake_lensstack
    lensstack.z.move(3)
    assert lensstack.z.position == 3


def test_read_lens_file(fake_lensstack):
    logger.debug('test_read_lens_file')
    lensstack = fake_lensstack
    assert lensstack.lens_set == sample_lens_set


def test_create_lens_file(fake_lensstack):
    logger.debug('test_create_lens_file')
    lensstack = fake_lensstack
    lensstack.create_lens(lensstack.lens_set)
    # Check that a backup was made
    assert os.path.exists(lensstack.backup_path)
    # Clean up the backup
    os.remove(lensstack.backup_path)
    # Check that the file we wrote is correct
    assert lensstack.read_lens() == sample_lens_set


def test_make_safe(fake_lensstack):
    logger.debug('test_make_safe')
    lens = fake_lensstack
    assert lens._make_safe()
    lens._att_obj = None
    assert not lens._make_safe()


@pytest.mark.timeout(5)
def test_xfls_disconnected():
    logger.debug('test_xfls_disconnected')
    XFLS('TST', name='tst')


@pytest.mark.timeout(5)
def test_prefocus_disconnected():
    logger.debug('test_prefocus_disconnected')
    Prefocus('TST', name='test')


@pytest.mark.timeout(5)
def test_lens_stack_disconnected(fake_att):
    logger.debug('test_xfls_disconnected')
    LensStack(name='test', x_prefix='x_motor', y_prefix='y_motor',
              z_prefix='z_motor', path=sample_lens_file, E=sample_E,
              z_offset=.01, z_dir=1, att_obj=fake_att)
