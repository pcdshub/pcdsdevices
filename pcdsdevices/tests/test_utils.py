import logging
import sys
import threading
import time
from decimal import Decimal

import pytest
from ophyd import Component as Cpt
from ophyd import Device, Signal

from .. import utils
from ..device import GroupDevice
from ..pv_positioner import PVPositionerDone
from ..utils import (
    generate_scan_points,
    move_subdevices_to_start,
    post_ophyds_to_elog,
    reorder_components,
    set_many,
    set_standard_ordering,
    sort_components_by_kind,
    sort_components_by_name,
)

try:
    import pty
except ImportError:
    pty = None


logger = logging.getLogger(__name__)
pty_missing = "Fails on Windows, pty not supported in Windows Python."


@pytest.fixture(scope="function")
def sim_input(monkeypatch):
    master, slave = pty.openpty()
    with open(slave) as fake_stdin:
        with open(master, "w") as sim_input:
            monkeypatch.setattr(sys, "stdin", fake_stdin)
            yield sim_input


def input_later(sim_input, inp, delay=0.1):
    def inner():
        time.sleep(delay)
        sim_input.write(inp)

    threading.Thread(target=inner, args=()).start()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
)
def test_is_input(sim_input):
    logger.debug("test_is_input")
    sim_input.write("a\n")
    assert utils.is_input()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
)
@pytest.mark.timeout(5)
def test_get_input_waits(sim_input):
    logger.debug("test_get_input_waits")
    input_later(sim_input, "a\n", delay=2)
    assert utils.get_input() == "a"


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
)
@pytest.mark.timeout(0.5)
def test_get_input_arrow(sim_input):
    logger.debug("test_get_input_arrow")
    input_later(sim_input, utils.arrow_up + "\n")
    assert utils.get_input() == utils.arrow_up


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
)
@pytest.mark.timeout(0.5)
def test_get_input_shift_arrow(sim_input):
    logger.debug("test_get_input_arrow")
    input_later(sim_input, utils.shift_arrow_up + "\n")
    assert utils.get_input() == utils.shift_arrow_up


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
)
@pytest.mark.timeout(0.5)
def test_cbreak(sim_input):
    logger.debug("test_cbreak")
    # send the ctrl+c character
    input_later(sim_input, "\x03\n")
    assert utils.get_input() == "\n"


def test_get_status_value():
    dummy_dictionary = {"dict1": {"dict2": {"value": 23}}}
    res = utils.get_status_value(dummy_dictionary, "dict1", "dict2", "value")
    assert res == 23
    res = utils.get_status_value(dummy_dictionary, "dict1", "dict2", "blah")
    assert res == "N/A"


def test_get_status_float():
    dummy_dictionary = {"dict1": {"dict2": {"value": 23.34343}}}
    res = utils.get_status_float(dummy_dictionary, "dict1", "dict2", "value")
    assert res == "23.3434"
    res = utils.get_status_float(dummy_dictionary, "dict1", "dict2", "blah")
    assert res == "N/A"
    res = utils.get_status_float(dummy_dictionary, "dict1", "dict2", "value", precision=3)
    assert res == "23.343"


class StatusDevice(Device):
    """simulate a device with a status method"""

    def status(self):
        return self.name


class BasicGroup(StatusDevice, GroupDevice):
    one = Cpt(StatusDevice, ":BASIC")
    two = Cpt(StatusDevice, ":COMPLEX")


class SomeDevice(StatusDevice):
    some = Cpt(StatusDevice, ":SOME")
    where = Cpt(StatusDevice, ":WHERE")


def test_ophyd_to_elog(elog):
    # make some devices

    group = BasicGroup("GROUP", name="group")
    some = SomeDevice("SOME", name="some")

    post_ophyds_to_elog([group, some], hutch_elog=elog)
    assert len(elog.posts) == 1
    # count number of content entries
    assert elog.posts[-1][0][0].count("<pre>") == 2

    post_ophyds_to_elog([group.one, some.some], hutch_elog=elog)
    assert len(elog.posts) == 1  # no children allowed by default

    post_ophyds_to_elog([[group, some], group.one, some.some], allow_child=True, hutch_elog=elog)
    assert len(elog.posts) == 2
    assert elog.posts[-1][0][0].count("<pre>") == 4
    # two list levels
    assert elog.posts[-1][0][0].count("class='parent'") == 2

    # half-hearted html validation
    for post in elog.posts:
        for tag in ["pre", "div", "button"]:
            assert post[0][0].count("<" + tag) == post[0][0].count("</" + tag)


class SampleSub(Device):
    sig = Cpt(Signal)


@pytest.fixture(scope="function")
def SampleClass():
    class SampleClass(Device):
        omit = Cpt(Signal, kind="omitted")
        cfg = Cpt(Signal, kind="config")
        norm = Cpt(Signal, kind="normal")
        hint = Cpt(Signal, kind="hinted")
        mot = Cpt(SampleSub, "MOT", kind="normal")
        sub = Cpt(SampleSub, "SUB", kind="hinted")

    return SampleClass


def get_order(cls):
    return list(cls._sig_attrs)


def test_reorder_components(SampleClass):
    reorder_components(SampleClass, start_with=["norm", SampleClass.sub], end_with=["hint", SampleClass.cfg])
    target_order = ["norm", "sub", "omit", "mot", "hint", "cfg"]
    assert get_order(SampleClass) == target_order
    reorder_components(SampleClass)
    assert get_order(SampleClass) == target_order


def test_normalize_reorder_list_errors(SampleClass):
    with pytest.raises(ValueError):
        reorder_components(SampleClass, start_with=[Cpt(Signal)])
    with pytest.raises(TypeError):
        reorder_components(SampleClass, start_with=[1])


def test_move_subdevices_to_start(SampleClass):
    move_subdevices_to_start(SampleClass)
    target_order = ["mot", "sub", "omit", "cfg", "norm", "hint"]
    assert get_order(SampleClass) == target_order


def test_sort_components_by_name(SampleClass):
    sort_components_by_name(SampleClass)
    target_order = sorted(["mot", "sub", "omit", "cfg", "norm", "hint"])
    assert get_order(SampleClass) == target_order


def test_sort_components_by_kind(SampleClass):
    sort_components_by_kind(SampleClass)
    target_order = ["hint", "sub", "norm", "mot", "cfg", "omit"]
    assert get_order(SampleClass) == target_order


def test_set_standard_ordering(SampleClass):
    set_standard_ordering(SampleClass)
    target_order = ["sub", "mot", "hint", "norm", "cfg", "omit"]
    assert get_order(SampleClass) == target_order


def test_reorder_decorators():
    @reorder_components(start_with=["cat"])
    class Pets(Device):
        dog = Cpt(Signal)
        cat = Cpt(Signal)

    assert get_order(Pets) == ["cat", "dog"]

    @move_subdevices_to_start(subdevice_cls=SampleSub)
    class Fruits(Device):
        apple = Cpt(Signal)
        banana = Cpt(SampleSub, "BANANA")

    assert get_order(Fruits) == ["banana", "apple"]

    @sort_components_by_name(reverse=True)
    class Veggies(Device):
        celery = Cpt(Signal)
        lettuce = Cpt(Signal)

    assert get_order(Veggies) == ["lettuce", "celery"]

    @sort_components_by_kind
    class Colors(Device):
        blue = Cpt(Signal, kind="normal")
        red = Cpt(Signal, kind="hinted")

    assert get_order(Colors) == ["red", "blue"]

    @set_standard_ordering
    class ChessPieces(Device):
        pawn = Cpt(Signal, kind="omitted")
        king = Cpt(Signal, kind="hinted")
        queen = Cpt(SampleSub, kind="hinted")
        knight = Cpt(Signal, kind="config")
        rook = Cpt(SampleSub, kind="normal")
        bishop = Cpt(Signal, kind="config")

    assert get_order(ChessPieces) == ["queen", "rook", "king", "bishop", "knight", "pawn"]


def test_set_many():
    """Checks that set_many sets multiple ophyd objects, and that it works
    with signals as well as positioners.

    Positioners and signals need different keyword arguments to their
    ``set()`` methods, so this implicitly tests that those are done
    properly.

    """

    # Create a dummy positioner with an extra signal
    class MyPositioner(PVPositionerDone):
        setpoint = Cpt(Signal)
        another_signal = Cpt(Signal)

    device = MyPositioner("", name="device")
    assert device.done.get() == 0
    # Set the positioner and the extra signal together
    st = set_many({device: 5, device.another_signal: 7}, raise_on_set_failure=True)
    st.wait(timeout=3)
    # Check that all the signals were set properly
    assert device.done.get() == 1
    assert device.setpoint.get() == 5
    assert device.another_signal.get() == 7


@pytest.mark.parametrize(
    "start,end,step,expected",
    [
        (1, 2, 0.25, ["1", "1.25", "1.50", "1.75", "2"]),
        (1, 2, 0.3, ["1", "1.3", "1.6", "1.9", "2"]),
        (0, 1, 0.5, ["0", "0.5", "1"]),
        (1, 2, 1, ["1", "2"]),
        (1, 2, 3, ["1", "2"]),
    ],
    ids=[
        "exact-steps",
        "short-final-step",
        "zero-start",
        "step-equals-interval",
        "step-exceeds-interval",
    ],
)
def test_forward_points(start, end, step, expected):
    points = list(generate_scan_points(start, end, step, 9, False))

    assert points == [Decimal(value) for value in expected]
    assert all(isinstance(point, Decimal) for point in points)


@pytest.mark.parametrize("step", [0.25, 0.3, 1, 3])
def test_bidirectional_retraces_forward_points_without_repeating_peak(step):
    forward = list(generate_scan_points(1, 2, step, 9, False))
    bidirectional = list(generate_scan_points(1, 2, step, 9, True))

    assert bidirectional == forward + forward[-2::-1]
    assert bidirectional.count(Decimal("2")) == 1
    assert bidirectional[0] == bidirectional[-1] == Decimal("1")
    assert all(left != right for left, right in zip(bidirectional, bidirectional[1:]))


def test_float_inputs_do_not_introduce_binary_artifacts():
    points = list(generate_scan_points(0.1, 0.3, 0.1, 9, False))

    assert points == [
        Decimal("0.1"),
        Decimal("0.2"),
        Decimal("0.3"),
    ]


def test_decimal_inputs():
    points = list(
        generate_scan_points(
            Decimal("1.1"),
            Decimal("1.4"),
            Decimal("0.1"),
            9,
            False,
        )
    )

    assert points == [
        Decimal("1.1"),
        Decimal("1.2"),
        Decimal("1.3"),
        Decimal("1.4"),
    ]


@pytest.mark.parametrize(
    "start,end,step,prec",
    [
        (-1, 2, 0.1, 9),  # Negative start
        (0, -1, 0.1, 9),  # Negative end
        (1, 1, 0.1, 9),  # Equal boundaries
        (2, 1, 0.1, 9),  # Reversed boundaries
        (1, 2, 0, 9),  # Zero step
        (1, 2, -0.1, 9),  # Negative step
        (1, 2, 0.1, 0),  # Zero precision
        (1, 2, 0.1, -1),  # Negative precision
        (1, 2, 0.1, 1.5),  # Non-integer precision
        (1, 2, 0.1, "9"),  # String precision
    ],
)
def test_invalid_arguments_raise_value_error(start, end, step, prec):
    # Consume the generator to execute its validation.
    with pytest.raises(ValueError):
        list(generate_scan_points(start, end, step, prec, False))


@pytest.mark.parametrize("argument", ["start", "end", "step"])
@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_nonfinite_inputs_raise_value_error(argument, value):
    kwargs = {
        "start": 1,
        "end": 2,
        "step": 0.1,
        "prec": 9,
        "bidirectional": False,
    }
    kwargs[argument] = value

    with pytest.raises(ValueError, match="must be finite"):
        list(generate_scan_points(**kwargs))


def test_insufficient_precision_raises_instead_of_looping_forever():
    with pytest.raises(ValueError, match="prec is too small"):
        list(generate_scan_points(1, 2, 0.01, 1, False))
