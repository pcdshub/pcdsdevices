import logging
import sys
import threading
import time

import pytest
from ophyd import Component as Cpt
from ophyd import Device

from .. import utils
from ..device import GroupDevice
from ..utils import post_ophyds_to_elog

try:
    import pty
except ImportError:
    pty = None


logger = logging.getLogger(__name__)
pty_missing = "Fails on Windows, pty not supported in Windows Python."


@pytest.fixture(scope='function')
def sim_input(monkeypatch):
    master, slave = pty.openpty()
    with open(slave, 'r') as fake_stdin:
        with open(master, 'w') as sim_input:
            monkeypatch.setattr(sys, 'stdin', fake_stdin)
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
    logger.debug('test_is_input')
    sim_input.write('a\n')
    assert utils.is_input()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
    )
@pytest.mark.timeout(5)
def test_get_input_waits(sim_input):
    logger.debug('test_get_input_waits')
    input_later(sim_input, 'a\n', delay=2)
    assert utils.get_input() == 'a'


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
    )
@pytest.mark.timeout(0.5)
def test_get_input_arrow(sim_input):
    logger.debug('test_get_input_arrow')
    input_later(sim_input, utils.arrow_up + '\n')
    assert utils.get_input() == utils.arrow_up


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
    )
@pytest.mark.timeout(0.5)
def test_get_input_shift_arrow(sim_input):
    logger.debug('test_get_input_arrow')
    input_later(sim_input, utils.shift_arrow_up + '\n')
    assert utils.get_input() == utils.shift_arrow_up


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=pty_missing,
    )
@pytest.mark.timeout(0.5)
def test_cbreak(sim_input):
    logger.debug('test_cbreak')
    # send the ctrl+c character
    input_later(sim_input, '\x03\n')
    assert utils.get_input() == '\n'


def test_get_status_value():
    dummy_dictionary = {'dict1': {'dict2': {'value': 23}}}
    res = utils.get_status_value(dummy_dictionary, 'dict1', 'dict2', 'value')
    assert res == 23
    res = utils.get_status_value(dummy_dictionary, 'dict1', 'dict2', 'blah')
    assert res == 'N/A'


def test_get_status_float():
    dummy_dictionary = {'dict1': {'dict2': {'value': 23.34343}}}
    res = utils.get_status_float(dummy_dictionary, 'dict1', 'dict2', 'value')
    assert res == '23.3434'
    res = utils.get_status_float(dummy_dictionary, 'dict1', 'dict2', 'blah')
    assert res == 'N/A'
    res = utils.get_status_float(
        dummy_dictionary, 'dict1', 'dict2', 'value', precision=3
    )
    assert res == '23.343'


class StatusDevice(Device):
    """ simulate a device with a status method """
    def status(self):
        return self.name


class BasicGroup(StatusDevice, GroupDevice):
    one = Cpt(StatusDevice, ':BASIC')
    two = Cpt(StatusDevice, ':COMPLEX')


class SomeDevice(StatusDevice):
    some = Cpt(StatusDevice, ':SOME')
    where = Cpt(StatusDevice, ':WHERE')


def test_ophyd_to_elog(elog):
    # make some devices

    group = BasicGroup('GROUP', name='group')
    some = SomeDevice('SOME', name='some')

    post_ophyds_to_elog([group, some], hutch_elog=elog)
    assert len(elog.posts) == 1
    # count number of content entries
    assert elog.posts[-1][0][0].count('<pre>') == 2

    post_ophyds_to_elog([group.one, some.some], hutch_elog=elog)
    assert len(elog.posts) == 1  # no children allowed by default

    post_ophyds_to_elog([[group, some], group.one, some.some],
                        allow_child=True, hutch_elog=elog)
    assert len(elog.posts) == 2
    assert elog.posts[-1][0][0].count('<pre>') == 4
    # two list levels
    assert elog.posts[-1][0][0].count("class='parent'") == 2

    # half-hearted html validation
    for post in elog.posts:
        for tag in ['pre', 'div', 'button']:
            assert post[0][0].count('<'+tag) == post[0][0].count('</'+tag)
