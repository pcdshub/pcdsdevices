import logging

import pytest
from bluesky import RunEngine
from bluesky.preprocessors import fly_during_wrapper, run_wrapper
from bluesky.plan_stubs import sleep
from ophyd.sim import NullStatus, make_fake_device

from pcdsdevices.sequencer import EventSequencer

logger = logging.getLogger(__name__)
FakeSequencer = make_fake_device(EventSequencer)


@pytest.fixture(scope='function')
def sequence():
    seq = FakeSequencer('ECS:TST', name='seq')
    # Running forever
    seq.play_mode.put(2)
    seq.play_control.put(0)
    return seq


# Simulated Sequencer for use in scans
class SimSequencer(FakeSequencer):
    """Simulated Sequencer usable in bluesky plans"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forces an immediate stop on complete
        self.play_mode.put(2)

    def kickoff(self):
        super().kickoff()
        return NullStatus()


def test_kickoff(sequence):
    logger.debug('test_kickoff')
    seq = sequence
    st = seq.kickoff()
    # Not currently playing
    seq.play_status.sim_put(0)
    # Check we gave the command to start the sequencer
    assert seq.play_control.get() == 1
    # Check that our monitors have started
    assert len(seq.current_step._callbacks['value']) == 1
    assert len(seq.play_count._callbacks['value']) == 1
    # Our status should not be done until the sequencer starts
    assert not st.done
    seq.play_status.sim_put(2)
    assert st.done
    assert st.success


def test_complete_run_forever(sequence):
    logger.debug('test_complete_run_forever')
    seq = sequence
    seq._acquiring = True
    # Run Forever mode should tell this to stop
    st = seq.complete()
    assert seq.play_control.value == 0
    assert st.done
    assert st.success


def test_complete_run_once(sequence):
    logger.debug('test_complete_run_once')
    seq = sequence
    seq._acquiring = True
    # Start the sequencer in run once mode
    seq.play_mode.put(0)
    seq.play_status.sim_put(2)
    st = seq.complete()
    # Our status should not be done until the sequence stops naturally
    assert not st.done
    seq.play_status.sim_put(0)
    assert st.done
    assert st.success


def test_pause_and_resume(sequence):
    seq = sequence
    # Start the sequence
    seq._acquiring = True
    seq.play_control.sim_put(1)
    # Assert we stopped our sequencer
    seq.pause()
    assert seq.play_control.get() == 0
    seq.resume()
    # Assert we restarted our sequencer
    assert seq.play_control.get() == 1


def test_fly_scan_smoke():
    seq = SimSequencer('ECS:TST', name='seq')
    RE = RunEngine()

    # Create a plan where we fly for a second
    def plan():
        yield from fly_during_wrapper(run_wrapper(sleep(1)), [seq])

    # Run the plan
    RE(plan())
