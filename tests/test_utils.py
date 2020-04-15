import logging
import pty
import sys
import threading
import time

import pcdsdevices.utils as util
import pytest

logger = logging.getLogger(__name__)


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


def test_is_input(sim_input):
    logger.debug('test_is_input')
    sim_input.write('a\n')
    assert util.is_input()


@pytest.mark.timeout(5)
def test_get_input_waits(sim_input):
    logger.debug('test_get_input_waits')
    input_later(sim_input, 'a\n', delay=2)
    assert util.get_input() == 'a'


@pytest.mark.timeout(0.5)
def test_get_input_arrow(sim_input):
    logger.debug('test_get_input_arrow')
    input_later(sim_input, util.arrow_up + '\n')
    assert util.get_input() == util.arrow_up


@pytest.mark.timeout(0.5)
def test_get_input_shift_arrow(sim_input):
    logger.debug('test_get_input_arrow')
    input_later(sim_input, util.shift_arrow_up + '\n')
    assert util.get_input() == util.shift_arrow_up


@pytest.mark.timeout(0.5)
def test_cbreak(sim_input):
    logger.debug('test_cbreak')
    # send the ctrl+c character
    input_later(sim_input, '\x03\n')
    assert util.get_input() == '\n'
