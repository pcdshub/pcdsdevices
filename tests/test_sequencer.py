from bluesky import RunEngine
from bluesky.preprocessors import fly_during_wrapper, run_wrapper
from bluesky.plan_stubs import sleep
from ophyd.sim import NullStatus

from pcdsdevices.sequencer import EventSequencer
from pcdsdevices.sim.pv import using_fake_epics_pv


def sequence():
    seq = EventSequencer('ECS:TST', name='seq')
    seq.wait_for_connection()
    # Running forever
    seq.play_mode.put(2)
    return seq


# Simulated Sequencer for use in scans
class SimSequencer(EventSequencer):
    """Simulated Sequencer usable in bluesky plans"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forces an immediate stop on complete
        self.play_mode.put(2)

    def kickoff(self):
        super().kickoff()
        return NullStatus()


@using_fake_epics_pv
def test_kickoff():
    seq = sequence()
    st = seq.kickoff()
    # Not currently playing
    seq.play_status._read_pv.put(0)
    seq.play_status._read_pv.run_callbacks()
    # Check we gave the command to start the sequencer
    assert seq.play_control.value == 1
    # Check that our monitors have started
    assert len(seq.current_step._callbacks['value']) == 1
    assert len(seq.play_count._callbacks['value']) == 1
    # Our status should not be done until the sequencer starts
    assert not st.done
    seq.play_status._read_pv.put(2)
    seq.play_status._read_pv.run_callbacks()
    assert st.done
    assert st.success


@using_fake_epics_pv
def test_complete_run_forever():
    seq = sequence()
    # Run Forever mode should tell this to stop
    st = seq.complete()
    assert seq.play_control.value == 0
    assert st.done
    assert st.success


@using_fake_epics_pv
def test_complete_run_once():
    seq = sequence()
    # Start the sequencer in run once mode
    seq.play_mode.put(0)
    seq.play_status._read_pv.put(2)
    seq.play_status._read_pv.run_callbacks()
    st = seq.complete()
    # Our status should not be done until the sequence stops naturally
    assert not st.done
    seq.play_status._read_pv.put(0)
    seq.play_status._read_pv.run_callbacks()
    assert st.done
    assert st.success


@using_fake_epics_pv
def test_fly_scan_smoke():
    seq = SimSequencer('ECS:TST', name='seq')
    RE = RunEngine()

    # Create a plan where we fly for a second
    def plan():
        yield from fly_during_wrapper(run_wrapper(sleep(1)), [seq])

    # Run the plan
    RE(plan())
