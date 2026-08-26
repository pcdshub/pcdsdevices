import pytest
from ophyd.sim import make_fake_device

from ..device import ObjectComponent as OCpt
from ..lxe import Lcls2LaserTiming
from ..pseudopos import SimDelayStage, SyncAxis
from .test_lxe import wrap_pv_positioner_move


# functions from RIX
def shift_t0(shift, lxt_ttc):
    """
    this function zeros lxt_ttc and shifts lxt by the amount passed (in seconds).
    """
    lxt = lxt_ttc.lxt
    txt = lxt_ttc.txt

    lxt_ttc.mv(0)
    lxt.mvr(shift)
    lxt_ttc.set_current_position(0)
    txt_position = txt.position
    msg = "moved lxt offset by " + str(shift*1E12) + "ps to compensate for drift. Current position of txt for lxt_ttc=0: " + str(txt_position)
    print(msg)
    return txt_position


def get_timing(lxt_ttc):
    lxt = lxt_ttc.lxt
    txt = lxt_ttc.txt
    """
    Get current positions of laser timing variables.
    log - boolean to log the positions in the elog
    msg - optional argument to append a message to the elog with the KB positions
    """
    curr_positions = {
        "lxt pos [ps]": lxt.wm()*1e12,
        "txt pos [ps]": txt.wm()*1e12,
        "lxt_ttc pos [ps]": lxt_ttc.wm()*1e12,
        "lxt offset [ns]": lxt.get()[3]*1e9,
        "lxt total delay [ns]": (lxt.get()[3] - lxt.get()[0]) * 1e9,
        "txt user stage [mm]": txt.get()[1],
    }
    __import__('pprint').pprint(curr_positions)


@pytest.fixture
def lxt_ttc_2(monkeypatch):

    lxt_2 = make_fake_device(Lcls2LaserTiming)(prefix='notreal', name='lxt',
                                               limits=(-10e-6, 10e-6))
    lxt_2._tgt_time.sim_set_limits(lxt_2.limits)
    lxt_2._tgt_time.sim_put(0)
    wrap_pv_positioner_move(monkeypatch, lxt_2)

    smaract = SimDelayStage('not_real', name='txt', limits=(-10e-6, 10e-6))

    class LXTTTC_TEST(SyncAxis):
        tab_component_names = True
        scales = {'txt': 1}
        warn_deadband = 5e-14
        fix_sync_keep_still = 'lxt'
        sync_limits = (-10e-6, 10e-6)

        lxt = OCpt(lxt_2)
        txt = OCpt(smaract)  # DELAY STAGE

    return LXTTTC_TEST('', name='tst')


def test_lxt_ttc_limits(lxt_ttc_2):
    shift = 8e-6
    shift_t0(shift, lxt_ttc_2)
    assert lxt_ttc_2.position[0] == 0

    # Normal Move w/ Shift
    new_position = -5e-6
    lxt_ttc_2.move(new_position)
    assert abs(lxt_ttc_2.position[0] - new_position) <= 0.1

    # Move back to 0
    lxt_ttc_2.move(0)
    assert lxt_ttc_2.position[0] == 0

    # Move txt out of bounds
    with pytest.raises(ValueError):
        lxt_ttc_2.mv(-10e-6)

    # Move lxt out of bounds
    with pytest.raises(ValueError):
        lxt_ttc_2.mv(10e-6)
