import pytest
from ophyd.device import Component as Cpt
from ophyd.signal import Signal

from pcdsdevices.pv_positioner import PVPositionerNoInterrupt


class PVPositionerNoInterruptLocal(PVPositionerNoInterrupt):
    setpoint = Cpt(Signal)
    done = Cpt(Signal)


@pytest.fixture(scope="function")
def pvpos_no(request):
    return PVPositionerNoInterruptLocal(name=request.node.name)


def test_pvpos_no_motion(pvpos_no):
    pvpos_no.done.put(1)
    status = pvpos_no.move(100, wait=False)
    # This is kind of silly but let's sim the full move
    pvpos_no.done.put(0)
    pvpos_no.done.put(1)
    assert pvpos_no.setpoint.get() == 100
    status.wait(timeout=1.0)
    assert status.done
    assert status.success


def test_pvpos_no_interrupt(pvpos_no):
    # Already moving, can't start a new one
    pvpos_no.done.put(0)
    with pytest.raises(RuntimeError):
        pvpos_no.move(100, wait=False)
