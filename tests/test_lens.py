import logging
from unittest.mock import Mock

from ophyd.sim import make_fake_device
import pytest

from pcdsdevices.lens import XFLS, LensStack, SimLensStack

from conftest import HotfixFakeEpicsSignal, fake_att

logger = logging.getLogger(__name__)

sample_lensset = (2, 200e-6, 4, 500e-6)
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


def test_LensStack_align(presets, monkeypatch):
    logger.debug('test_LensStack_align')

    def mocktweak(self):
        lens.x.move(lens.x.position+1)
        lens.y.move(lens.y.position+1)
    lens = SimLensStack(name='test',
                        x_prefix='x_motor',
                        y_prefix='y_motor',
                        z_prefix='z_motor')
    monkeypatch.setattr(LensStack, 'tweak', mocktweak)
    lens.align(0)
    assert lens.z.position == 0
    assert lens.x.position == 1.5
    assert lens.y.position == 1.5


def test_setup_path(monkeypatch):
    logger.debug('test_setup_path')
    monkeypatch.setattr('builtins.input', lambda x: "some input")
    i = input("expected input")
    assert i == "some input"
    monkeypatch.setattr("pcdsdevices.lens.setup_path", lambda x: " ")
    lens = fake_lenscalcbase()
    lens.lens_path = setup_path()
    assert lens.lens_path == i


def test_readLensFile(tmpdir):
    logger.debug('test_readLensFile')
    p = tmpdir.mkdir("sub").join("lensfile.yaml")
    p.write("[2,200e-6,4,500e-6]")
    assert p.read() == "[2,200e-6,4,500e-6]"
    m = tmpdir.join("lensfilecopy.yaml")
    m.write("[2,200e-6,4,500e-6]")
    assert m.read() == "[2,200e-6,4,500e-6]"


def test_CreateLensFile(tmpdir, monkeypatch):
    logger.debug('test_CreateLensFile')
    p = tmpdir.mkdir("sub").join("lensfile.yaml")
    monkeypatch.setattr('builtins.input', lambda x: "[2,200e-6,4,500e-6]")
    i = input("lensset : ")
    p.write(i)
    assert p.read() == "[2,200e-6,4,500e-6]"


def test_calcFocalLength(monkeypatch, tmpdir):
    logger.debug('test_calcFocalLength')
    lens = fake_lenscalcbase()
    # lensset = test_getlens(tmpdir,monkeypatch)
    number = lens.calcFocalLength(lens._E, (2, 200e-6, 4, 500e-6))
    assert number == 5.2150594897480556


def test_calcFocalLengthForSingleLens():
    logger.debug('test_calcFocalLengthForSingleLens')
    lens = fake_lenscalcbase()
    f = lens.calcFocalLengthForSingleLens(lens._E, .0001)
    assert f == 9.387107081546501


def test_getDelta():
    logger.debug('test_getDelta')
    lens = fake_lenscalcbase()
    assert lens.getDelta(E=sample_E) == 5.326454632470501e-06


def test_calcBeamFWHM(monkeypatch):
    logger.debug('test_calcBeamFWH')
    lens = fake_lenscalcbase()
    h = lens.calcBeamFWHM(8, sample_lensset, distance=4, fwhm_unfocused=500e-6)
    assert h == 0.00011649743222659306


def test_getlens(tmpdir, monkeypatch):
    logger.debug('test_getlens')
    lens = fake_lenscalcbase()
    if type(lens.lensset) == tuple:
        lens.lensset = test_CreateLensFile(tmpdir, monkeypatch)
    else:
        lens.lensset = test_readLensFile()
    return lens.lensset


def test_moveBeamSize(monkeypatch):
    logger.debug('test_moveBeamSize')
    lens = fake_lenscalcbase()
    lens._moveBeamsize(.01, True, sample_lensset)
    lens._zoffset = None
    lens._zdir = None
    lens.beamsizeUnfocused = None
    assert lens._moveBeamsize(.01, True, sample_lensset) is None


def test_whereBeamSize():
    logger.debug('test_whereBeamSize')
    lens = fake_lenscalcbase()
    lens._whereBeamsize(lens.lensset)
    lens._zoffset = None
    lens._zdir = None
    lens._beamsizeUnfocused = None
    assert lens._whereBeamsize(lens.lensset) is None


def test_moveZ():
    logger.debug('test_moveZ')
    lens = fake_lenscalcbase()
    lens._moveZ(1, True)
    lens.calib_z == .1
    lens._moveZ(1, False)


def test_makeSafe():
    logger.debug('test_makeSafe')
    lens = fake_lenscalcbase()
    lens._attObj = fake_att()
    assert lens._makeSafe() is True


def test_calcDistanceForSize(monkeypatch):
    logger.debug('test_calcDistanceForSize')
    lens = fake_lenscalcbase()
    lens.calcDistanceForSize(.1, sample_lensset, E=8, fwhm_unfocused=500e-6)


def test_setE(monkeypatch):
    logger.debug('test_setE')
    lens = fake_lenscalcbase()
    f = lens.set_E(energy=1.0)
    assert lens.set_E(1.0) == f


def fake_lenscalcbase():
    fake_lenscalcbase = SimLensStack(name='test', x_prefix='x_motor',
                                     y_prefix='y_motor', z_prefix='z_motor',
                                     lensset=sample_lensset,
                                     lens_path='/reg/neh/home/tmp', E=sample_E,
                                     _zoffset=.01, zdir=1, zrange=None,
                                     precisionLateral=0.05, attObj=None,
                                     lclsObj=.01, monoObj=.01,
                                     beamsizeUnfocused=500e-6, calib_z=None)
    return fake_lenscalcbase
