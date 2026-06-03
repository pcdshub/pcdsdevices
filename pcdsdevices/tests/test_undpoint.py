"""
Make sure the simulated undulator devices are self-consistent
"""
import time

import pytest

from pcdsdevices.undpoint import (SafeUndPointAbs2DSim, UndPointAbs2DSim,
                                  UndPointDelta2DSim)


def wait_assert_approx(getter, answer, timeout=2.0):
    segm = 10
    for _ in range(segm):
        if getter() == pytest.approx(answer):
            break
        time.sleep(timeout / segm)
    assert getter() == pytest.approx(answer)


def test_undpoint_delta_2d_sim():
    undp = UndPointDelta2DSim("DELTA:SIM", name="delta_sim")
    undp.move(10, 20)
    wait_assert_approx(undp._raw_x.get, 0.01)
    wait_assert_approx(undp._raw_y.get, 0.02)
    undp.move(-100, -200)
    wait_assert_approx(undp._raw_x.get, -0.09)
    wait_assert_approx(undp._raw_y.get, -0.18)


def test_undpoint_abs_2d_sim():
    undp = UndPointAbs2DSim("ABS:SIM", name="delta_sim")
    undp.move(10, 20)
    wait_assert_approx(lambda: undp.position, (10, 20))
    undp.move(-20, -50)
    wait_assert_approx(lambda: undp.position, (-20, -50))


def test_undpoint_safe_abs_2d_sim():
    undp = SafeUndPointAbs2DSim("SAFE:SIM", name="delta_sim")
    # Set a starting point
    undp.delta_xy._raw_x.put(0)
    undp.delta_xy._raw_y.put(0)
    # Small move: no steps
    undp.move(0.01, -0.02)
    wait_assert_approx(lambda: undp.position, (0.01, -0.02))
    # Big enough for steps
    undp.move(10, -20)
    wait_assert_approx(lambda: undp.position, (10, -20))
