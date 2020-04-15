import logging
import os
import os.path
from unittest.mock import Mock

import numpy as np
import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.lens import XFLS, LensStack, LensStackBase, SimLensStack

logger = logging.getLogger(__name__)

sample_lens_file = os.path.dirname(__file__) + '/test_lens_sets/test.yaml'
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
    xfls = fake_xfls
    # Subscribe a pseudo callback
    cb = Mock()
    xfls.subscribe(cb, event_type=xfls.SUB_STATE, run=False)
    # Change readback state
    xfls.state.put(4)
    assert cb.called


@pytest.fixture(scope='function')
def fake_lensstack(fake_att):
    fake_lensstack = SimLensStack(name='test', x_prefix='x_motor',
                                  y_prefix='y_motor', z_prefix='z_motor',
                                  path=sample_lens_file,
                                  E=sample_E,
                                  z_offset=.01, z_dir=1, att_obj=fake_att,
                                  lcls_obj=.01, mono_obj=.01,
                                  beamsize_unfocused=500e-6)
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


def test_calc_focal_length(fake_lensstack):
    logger.debug('test_calc_focal_length')
    lens = fake_lensstack
    number = lens.calc_focal_length(lens._E, (2, 200e-6, 4, 500e-6))
    assert np.isclose(number, 5.2150594897480556)


def test_calc_focal_length_for_single_lens(fake_lensstack):
    logger.debug('test_calc_focal_length_for_single_lens')
    lens = fake_lensstack
    f = lens.calc_focal_length_for_single_lens(lens._E, .0001)
    assert np.isclose(f, 9.387107081546501)


def test_get_delta(fake_lensstack):
    logger.debug('test_get_delta')
    lens = fake_lensstack
    assert np.isclose(lens.get_delta(E=sample_E), 5.326454632470501e-06)


def test_calc_beam_fwhm(fake_lensstack):
    logger.debug('test_calc_beam_fwhm')
    lens = fake_lensstack
    h = lens.calc_beam_fwhm(8, sample_lens_set, distance=4,
                            fwhm_unfocused=500e-6)
    assert np.isclose(h, 0.00011649743222659306)


def test_make_safe(fake_lensstack):
    logger.debug('test_make_safe')
    lens = fake_lensstack
    assert lens._make_safe()
    lens._att_obj = None
    assert not lens._make_safe()


def test_calc_distance_for_size(fake_lensstack):
    logger.debug('test_calc_distance_for_size')
    lens = fake_lensstack
    dist = lens.calc_distance_for_size(.1, sample_lens_set, E=8,
                                       fwhm_unfocused=500e-6)
    assert all(np.isclose(dist, [-1037.79683843, 1048.22695741]))


@pytest.mark.timeout(5)
def test_xfls_disconnected():
    XFLS('TST', name='tst')


@pytest.mark.timeout(5)
def test_lens_stack_disconnected():
    LensStack(name='test',
              x_prefix='x_motor',
              y_prefix='y_motor',
              z_prefix='z_motor',
              path=sample_lens_file)
