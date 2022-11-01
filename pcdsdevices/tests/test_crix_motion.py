import functools

import numpy as np
import pytest

from ..crix_motion import VLSOpticsSim

# Calculation answers
# Component = (mm, mrad)
vls_mirror_lower = (-1.179, 5.275)
vls_mirror_upper = (0.813, 41.882)
vls_grating_lower = (-1.74, 51.8462)
vls_grating_upper = (1.2, 3.5410)


@pytest.fixture(scope='function')
def vls():
    return VLSOpticsSim(name='vls')


# Example vals only accurate to 2 decimal places at worst
# Use a less strict comparison for the accuracy checks
acc_isclose = functools.partial(np.isclose, atol=0.004)


def test_calc_reverses(vls):
    for optic in (vls.mirror, vls.grating):
        lower_mrad, upper_mrad = optic.calc.limits
        lower_mm = optic.forward(lower_mrad)
        upper_mm = optic.forward(upper_mrad)
        assert np.isclose(lower_mrad, optic.inverse(lower_mm))
        assert np.isclose(upper_mrad, optic.inverse(upper_mm))


def test_calc_accuracy(vls):
    def compare(pseudopos, answer):
        forward_calc = pseudopos.forward(answer[1])[0]
        assert acc_isclose(forward_calc, answer[0])
        inverse_calc = pseudopos.inverse(answer[0])[0]
        assert acc_isclose(inverse_calc, answer[1])

    compare(vls.mirror, vls_mirror_lower)
    compare(vls.mirror, vls_mirror_upper)
    compare(vls.grating, vls_grating_lower)
    compare(vls.grating, vls_grating_upper)


def test_move_consistency(vls):
    for optic in (vls.mirror, vls.grating):
        lower_mrad, upper_mrad = optic.calc.limits
        optic.move(lower_mrad)
        assert np.isclose(optic.position[0], lower_mrad)
        optic.move(upper_mrad)
        assert np.isclose(optic.position[0], upper_mrad)


def test_move_accuracy(vls):
    def test_real_move(pseudopos, answer):
        pseudopos.real.move(answer[0])
        assert acc_isclose(pseudopos.calc.position, answer[1])

    def test_pseudo_move(pseudopos, answer):
        pseudopos.calc.move(answer[1])
        assert acc_isclose(pseudopos.real.position, answer[0])

    def test_moves(pseudopos, answer):
        test_real_move(pseudopos, answer)
        test_pseudo_move(pseudopos, answer)

    test_moves(vls.mirror, vls_mirror_lower)
    test_moves(vls.mirror, vls_mirror_upper)
    test_moves(vls.grating, vls_grating_lower)
    test_moves(vls.grating, vls_grating_upper)
