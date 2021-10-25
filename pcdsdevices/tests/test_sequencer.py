import logging

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import sleep
from bluesky.preprocessors import fly_during_wrapper, run_wrapper
from ophyd.sim import NullStatus, make_fake_device

from ..sequencer import EventSequencer

logger = logging.getLogger(__name__)

FakeSequencer = make_fake_device(EventSequencer)


@pytest.fixture(scope='function')
def sequence():
    seq = FakeSequencer('ECS:TST:100', name='seq')
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
        # Initialize all signals to *something* to appease bluesky
        # Otherwise, these are all None which is invalid
        self.play_control.sim_put(0)
        self.sequence_length.sim_put(0)
        self.current_step.sim_put(0)
        self.play_count.sim_put(0)
        self.play_status.sim_put(0)
        self.sync_marker.sim_put(0)
        self.next_sync.sim_put(0)
        self.pulse_req.sim_put(0)
        self.sequence_owner.sim_put(0)
        self.sequence.ec_array.sim_put([0] * 2048)
        self.sequence.bd_array.sim_put([0] * 2048)
        self.sequence.fd_array.sim_put([0] * 2048)
        self.sequence.bc_array.sim_put([0] * 2048)

        # Initialize sequence
        initial_sequence = [[0] * 20,
                            [0] * 20,
                            [0] * 20,
                            [0] * 20]
        self.sequence.put_seq(initial_sequence)

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
    st.wait(timeout=1)
    assert st.done
    assert st.success


def test_trigger(sequence):
    # Not currently playing
    sequence.play_status.sim_put(0)
    # Set to run forever
    sequence.play_mode.put(2)
    trig_status = sequence.trigger()
    # Sequencer has started
    assert sequence.play_control.get() == 1
    # Trigger is automatically complete
    trig_status.wait(timeout=1)
    assert trig_status.done
    assert trig_status.success
    # Stop sequencer
    # Not currently playing
    sequence.play_status.sim_put(0)
    sequence.play_control.put(0)
    # Set to run once
    sequence.play_mode.put(0)
    trig_status = sequence.trigger()
    # Simulate the sequence starting
    sequence.play_status.sim_put(2)
    # Not done until sequencer is done
    assert sequence.play_control.get() == 1
    assert not trig_status.done
    # Simulate the sequence ending
    sequence.play_status.sim_put(0)
    trig_status.wait(timeout=1)
    assert trig_status.done
    assert trig_status.success


def test_complete_run_forever(sequence):
    logger.debug('test_complete_run_forever')
    seq = sequence
    seq._acquiring = True
    # Run Forever mode should tell this to stop
    st = seq.complete()
    assert seq.play_control.get() == 0
    st.wait(timeout=1)
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
    st.wait(timeout=1)
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


@pytest.mark.xfail()
def test_fly_scan_smoke():
    seq = SimSequencer('ECS:TST:100', name='seq')
    RE = RunEngine()

    # Create a plan where we fly for a second
    def plan():
        yield from fly_during_wrapper(run_wrapper(sleep(1)), [seq])

    # Run the plan
    RE(plan())


def test_sequence_get_put():
    seq = SimSequencer('ECS:TST:100', name='seq')

    dummy_sequence = [[1,  2,  3,  4],
                      [5,  6,  7,  8],
                      [9, 10, 11, 12],
                      [13, 14, 15, 16]]

    # Write the dummy sequence
    seq.sequence.put_seq(dummy_sequence)

    # Read back the sequence, and compare to dummy sequence
    curr_seq = seq.sequence.get_seq()

    assert curr_seq == dummy_sequence


@pytest.mark.timeout(5)
def test_seq_disconnected():
    EventSequencer('ECS:TST:100', name='seq')
