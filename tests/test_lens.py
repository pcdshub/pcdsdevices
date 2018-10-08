import logging
from unittest.mock import Mock

from ophyd.sim import make_fake_device
import pytest
import os 
from pcdsdevices.lens import XFLS, SimLensStack, LensStackBase

from conftest import HotfixFakeEpicsSignal, fake_att

logger = logging.getLogger(__name__)

sample_lens_set = (2, 200e-6, 4, 500e-6)
sample_E = 8


@pytest.fixture(scope='function')
def fake_xfls():
    FakeXFLS = make_fake_device(XFLS)
    FakeXFLS.state.cls = HotfixFakeEpicsSignal
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

def test_LensStackBeamsize(monkeypatch):
    logger.debug('test_LensStackBeamsize')
    lensstack = fake_lensstack()
    lensstack.beam_size.move(100e-6)
    lensstack._attObj = fake_att()
    def mocktweak(self):
        lensstack.x.move(lensstack.x.position+1)
        lensstack.y.move(lensstack.y.position+1)
    monkeypatch.setattr(LensStackBase, 'tweak', mocktweak)
    lensstack.align(0)
    assert lensstack.beam_size.position == 0.0004894541353076458
    lensstack.beam_size.set(.01)
    assert lensstack.beam_size.position == .01


def test_LensStack_align(presets, monkeypatch):
    logger.debug('test_LensStack_align')

    def mocktweak(self):
        lens.x.move(lens.x.position+1)
        lens.y.move(lens.y.position+1)
    lens = fake_lensstack()
    lens._attObj = fake_att()
    monkeypatch.setattr(LensStackBase, 'tweak', mocktweak)
    lens.align(0)
    assert lens.x.position == 1.5
    assert lens.y.position == 1.5
    assert lens.z.position == 0


def test_move():
    logger.debug('test_move')
    lensstack = fake_lensstack()
    if test_makeSafe() is True:
        lensstack.z.move(lensstack.z.position+3)
        assert lensstack.z.position == 3
    else:
        assert lensstack.z.position == lensstack.z.position


def test_readLensFile(tmpdir):
    logger.debug('test_readLensFile')
    p = tmpdir.mkdir("sub").join("lensfile.yaml")
    p.write("[2,200e-6,4,500e-6]")
    assert p.read() == "[2,200e-6,4,500e-6]"


def test_CreateLensFile(tmpdir, monkeypatch):
    logger.debug('test_CreateLensFile')
    lensstack = fake_lensstack()
    lensstack.CreateLens(lensstack.lens_set)
    p = tmpdir.mkdir("sub").join("lensfile.yaml")
    monkeypatch.setattr('builtins.input', lambda x: "[2,200e-6,4,500e-6]")
    i = input("lens_set : ")
    p.write(i)
    assert p.read() == "[2,200e-6,4,500e-6]"


def test_calcFocalLength(tmpdir):
    logger.debug('test_calcFocalLength')
    lens = fake_lensstack()
    number = lens.calcFocalLength(lens._E, (2, 200e-6, 4, 500e-6))
    assert number == 5.2150594897480556


def test_calcFocalLengthForSingleLens():
    logger.debug('test_calcFocalLengthForSingleLens')
    lens = fake_lensstack()
    f = lens.calcFocalLengthForSingleLens(lens._E, .0001)
    assert f == 9.387107081546501


def test_getDelta():
    logger.debug('test_getDelta')
    lens = fake_lensstack()
    assert lens.getDelta(E=sample_E) == 5.326454632470501e-06


def test_calcBeamFWHM():
    logger.debug('test_calcBeamFWH')
    lens = fake_lensstack()
    h = lens.calcBeamFWHM(8, sample_lens_set, distance=4, fwhm_unfocused=500e-6)
    assert h == 0.00011649743222659306


def test_makeSafe():
    logger.debug('test_makeSafe')
    lens = fake_lensstack()
    lens._attObj = fake_att()
    assert lens._makeSafe() is True
    lens._attObj = None
    assert lens._makeSafe() is False


def test_calcDistanceForSize(monkeypatch):
    logger.debug('test_calcDistanceForSize')
    lens = fake_lensstack()
    lens.calcDistanceForSize(.1, sample_lens_set, E=8, fwhm_unfocused=500e-6)


def fake_lensstack():
    fake_lensstack = SimLensStack(name='test', x_prefix='x_motor',
                                  y_prefix='y_motor', z_prefix='z_motor',
                                  path=os.path.dirname(__file__) + '/test_lens_set',
                                  E=sample_E,
                                  _zoffset=.01, zdir=1, attObj=None,
                                  lclsObj=.01, monoObj=.01,
                                  beamsizeUnfocused=500e-6)
    return fake_lensstack
