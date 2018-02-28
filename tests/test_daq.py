import time
import logging
import pytest

from ophyd.sim import SynSignal
from ophyd.status import wait as status_wait
from bluesky import RunEngine
from bluesky.plan_stubs import (trigger_and_read, sleep,
                                create, read, save, null)
from bluesky.preprocessors import run_decorator, run_wrapper

from pcdsdevices import daq as daq_module
from pcdsdevices.daq import (Daq, daq_wrapper, daq_decorator, calib_cycle,
                             BEGIN_TIMEOUT)
from pcdsdevices.sim import pydaq as sim_pydaq
from pcdsdevices.sim.pydaq import SimNoDaq

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def daq(RE):
    # Let's hack the daq module to use the simdaq
    daq_module.pydaq = sim_pydaq
    return Daq(RE=RE)


@pytest.fixture(scope='function')
def nodaq(RE):
    return SimNoDaq(RE=RE)


@pytest.fixture(scope='function')
def RE():
    RE = RunEngine({})
    RE.verbose = True
    return RE


@pytest.fixture(scope='function')
def sig():
    sig = SynSignal(name='test')
    sig.put(0)
    return sig


def test_connect(daq):
    """
    We expect connect to bring the daq from a disconnected state to a connected
    state.
    """
    logger.debug('test_connect')
    assert not daq.connected
    daq.connect()
    assert daq.connected
    daq.connect()  # Coverage
    # If something goes wrong...
    daq._control = None
    daq_module.pydaq = None
    daq.connect()
    assert daq._control is None


def test_disconnect(daq):
    """
    We expect disconnect to bring the daq from a connected state to a
    disconnected state.
    """
    logger.debug('test_disconnect')
    assert not daq.connected
    daq.connect()
    assert daq.connected
    daq.disconnect()
    assert not daq.connected


class Dummy:
    position = 4


def test_configure(daq, sig):
    """
    We expect the configured attribute to be correct.
    We expect a disconnected daq to connect and then configure.
    We expect a configure with no args to pick the defaults.
    We expect to be able to disconnect after a configure.
    We expect a connected daq to be able to configure.
    We expect configure to return both the old and new configurations.
    We expect read_configure to give us the current configuration, including
    default args.
    """
    logger.debug('test_configure')
    assert not daq.connected
    assert not daq.configured
    daq.configure()
    assert daq.config == daq.default_config
    assert daq.connected
    assert daq.configured
    daq.disconnect()
    assert not daq.connected
    assert not daq.configured
    daq.connect()
    assert daq.connected
    assert not daq.configured
    configs = [
        dict(events=1000, use_l3t=True),
        dict(events=1000, use_l3t=True, record=True),
        dict(duration=10, controls=dict(test=Dummy())),
    ]
    prev_config = daq.read_configuration()
    for config in configs:
        old, new = daq.configure(**config)
        assert old == prev_config
        assert daq.read_configuration() == new
        for key, value in config.items():
            assert daq.config[key] == value
        prev_config = daq.read_configuration()


@pytest.mark.timeout(10)
def test_basic_run(daq, sig):
    """
    We expect a begin without a configure to automatically configure
    We expect the daq to run for the time passed into begin
    We expect that we close the run upon calling end_run
    """
    logger.debug('test_basic_run')
    assert daq.state == 'Disconnected'
    daq.begin(duration=1, controls=[sig])
    assert daq.state == 'Running'
    time.sleep(1.3)
    assert daq.state == 'Open'
    daq.end_run()
    assert daq.state == 'Configured'
    daq.begin(events=1, wait=True, use_l3t=True)
    # now we force the kickoff to time out
    daq._control._state = 'Disconnected'
    start = time.time()
    status = daq.kickoff(duration=BEGIN_TIMEOUT+3)
    with pytest.raises(RuntimeError):
        status_wait(status, timeout=BEGIN_TIMEOUT+1)
    dt = time.time() - start
    assert dt < BEGIN_TIMEOUT + 1


@pytest.mark.timeout(3)
def test_stop_run(daq):
    """
    We expect the daq to run indefinitely if no time is passed to begin
    We expect that the running stops early if we call stop
    """
    logger.debug('test_stop_run')
    t0 = time.time()
    daq.begin()
    assert daq.state == 'Running'
    time.sleep(1.3)
    assert daq.state == 'Running'
    daq.stop()
    assert daq.state == 'Open'
    less_than_2 = time.time() - t0
    assert less_than_2 < 2


@pytest.mark.timeout(3)
def test_wait_run(daq):
    """
    We expect that wait will block the thread until the daq is no longer
    running
    We expect that a wait when nothing is happening will do nothing
    """
    logger.debug('test_wait_run')
    t0 = time.time()
    daq.wait()
    short_time = time.time() - t0
    assert short_time < 1
    t1 = time.time()
    daq.begin(duration=1)
    daq.wait()
    just_over_1 = time.time() - t1
    assert 1 < just_over_1 < 1.2
    t3 = time.time()
    daq.wait()
    short_time = time.time() - t3
    assert short_time < 1
    daq.end_run()


@pytest.mark.timeout(3)
def test_configured_run(daq, sig):
    """
    We expect begin() to run for the configured time, should a time be
    configured
    """
    logger.debug('test_configured_run')
    daq.configure(duration=1, controls=dict(sig=sig))
    t0 = time.time()
    daq.begin()
    daq.wait()
    just_over_1 = time.time() - t0
    assert 1 < just_over_1 < 1.2
    daq.end_run()


@pytest.mark.timeout(3)
def test_pause_resume(daq):
    """
    We expect pause and resume to work.
    """
    logger.debug('test_pause_resume')
    daq.begin(duration=5)
    assert daq.state == 'Running'
    daq.pause()
    assert daq.state == 'Open'
    daq.resume()
    assert daq.state == 'Running'
    daq.stop()
    assert daq.state == 'Open'
    daq.end_run()
    assert daq.state == 'Configured'


def test_daq_fixtures(daq, RE):
    """
    Verify that the test setup looks correct
    """
    logger.debug('test_daq_fixtures')
    assert daq._RE == RE


@pytest.mark.timeout(10)
def test_scan_on(daq, RE, sig):
    """
    We expect that the daq object is usable in a bluesky plan in the 'on' mode.
    """
    logger.debug('test_scan_on')

    @daq_decorator(mode='on')
    @run_decorator()
    def plan(reader):
        yield from null()
        for i in range(10):
            assert daq.state == 'Running'
            yield from trigger_and_read([reader])
        assert daq.state == 'Running'
        yield from null()

    RE(plan(sig))
    assert daq.state == 'Configured'


@pytest.mark.timeout(10)
def test_scan_manual(daq, RE, sig):
    """
    We expect that we can manually request calib cycles at specific times
    """
    logger.debug('test_scan_manual')

    @daq_decorator(mode=1)
    @run_decorator()
    def plan(reader):
        yield from sleep(0.1)
        for i in range(10):
            assert daq.state == 'Open'
            yield from calib_cycle(events=1)
        assert daq.state == 'Open'
        yield from null()

    RE(plan(sig))
    assert daq.state == 'Configured'


@pytest.mark.timeout(10)
def test_scan_auto(daq, RE, sig):
    """
    We expect that we can automatically get daq runs between create and save
    messages
    """
    logger.debug('test_scan_auto')

    @daq_decorator()
    @run_decorator()
    def plan(reader):
        logger.debug(daq.config)
        yield from null()
        for i in range(10):
            yield from create()
            assert daq.state == 'Running'
            yield from read(reader)
            yield from save()
            assert daq.state == 'Open'
        yield from null()

    daq.configure(mode='auto')
    RE(plan(sig))
    daq.configure(mode='auto', events=1)
    RE(plan(sig))
    assert daq.state == 'Configured'


@pytest.mark.timeout(10)
def test_post_daq_RE(daq, RE, sig):
    """
    We expect that the RE will be clean after running with the daq
    """
    logger.debug('test_post_daq_RE')

    @run_decorator()
    def plan(reader, expected):
        yield from null()
        for i in range(10):
            yield from create()
            assert daq.state == expected
            yield from read(reader)
            yield from save()
        yield from null()

    RE(daq_wrapper(plan(sig, 'Running')))
    RE(plan(sig, 'Configured'))
    assert daq.state == 'Configured'


def test_check_connect(nodaq):
    """
    If the daq can't connect for any reason, we should get an error on any
    miscellaneous method that has the check_connect wrapper.
    """
    logger.debug('test_check_connect')
    with pytest.raises(RuntimeError):
        nodaq.wait()


def test_bad_stuff(daq, RE):
    """
    Miscellaneous exception raises
    """
    logger.debug('test_bad_stuff')

    # Bad mode name
    with pytest.raises(ValueError):
        daq.configure(mode='cashews')

    # Daq internal error
    configure = daq._control.configure
    daq._control.configure = None
    with pytest.raises(RuntimeError):
        daq.configure()
    daq._control.configure = configure

    # Run is too short
    with pytest.raises(RuntimeError):
        daq._check_duration(0.1)

    # daq wrapper cleanup with a bad plan
    def plan():
        yield from null()
        raise RuntimeError
    with pytest.raises(Exception):
        list(daq_wrapper(run_wrapper(plan)))
    assert daq._RE.msg_hook is None

    # calib_cycle at the wrong time
    with pytest.raises(RuntimeError):
        list(calib_cycle())

    # calib_cycle with a bad config
    def plan():
        yield from calib_cycle()
    with pytest.raises(RuntimeError):
        RE(daq_wrapper(run_wrapper(plan())))

    # Configure during a run
    daq.begin(duration=1)
    with pytest.raises(RuntimeError):
        daq.configure()
    daq.end_run()  # Prevent thread stalling


def test_call_everything_else(daq, sig):
    """
    These are things that bluesky uses. Let's check them.
    """
    logger.debug('test_call_everything_else')
    daq.describe_configuration()
    daq.configure(controls=dict(sig=sig))
    daq.stage()
    daq.unstage()
