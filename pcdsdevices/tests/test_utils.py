import logging
import sys
import threading
import time

import pytest

from .. import utils

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
