import numpy as np
import pytest

from ..crix_motion import VLSOpticsSim


@pytest.fixture(scope='function')
def vls():
    return VLSOpticsSim(name='vls')


def test_calc_reverses(vls):
    for optic in (vls.mirror, vls.grating):
        lower_mrad, upper_mrad = optic.limits
        lower_mm = optic.forward(lower_mrad)
        upper_mm = optic.forward(upper_mrad)
        assert np.isclose(lower_mrad=optic.inverse(lower_mm))
        assert np.isclose(upper_mrad, optic.inverse(upper_mm))


def test_calc_accuracy(vls):
    pass


def test_move_consistency(vls):
    pass


def test_move_accuracy(vls):
    pass
