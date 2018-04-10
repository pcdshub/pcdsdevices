import time
import logging
from functools import partial

from ophyd import Device, EpicsSignal, EpicsSignalRO, Component as Cpt
from ophyd.status import DeviceStatus, SubscriptionStatus
from ophyd.utils.epics_pvs import raise_if_disconnected


logger = logging.getLogger(__name__)


class EventSequencer(Device):
    """
    Event Sequencer

    The LCLS Event Sequencer implemented as an Flyer; i.e it has the methods
    :meth:`.kickoff`, :meth:`.complete` and :meth:`.collect`. This allows the
    EventSequencer to be used succinctly with the `fly_during_wrapper` and
    associated preprocessor.

    Parameters
    ----------
    prefix: str
        Base prefix of the EventSequencer

    name : str
        Name of Event Sequencer object

    Examples
    --------
    Run the EventSequencer throughout my scan

    .. code::

        fly_during_wrapper(scan([det], motor, ...), [sequencer])

    Run the EventSequencer at each step in my scan, after the completing the
    motor move.

    .. code::

        def step_then_sequence(detectors, step, pos_cache)
            yield from one_nd_step(detectors, step, pos_cache)
            yield from kickoff(sequencer)
            yield from complete(sequencer)  # Waits for sequence to complete if
                                            # not in "Run Forever" mode

        scan([det], motor, ..., per_step=step_then_sequence)
    """
    play_control = Cpt(EpicsSignal, ':PLYCTL')
    sequence_length = Cpt(EpicsSignal, ':LEN')
    current_step = Cpt(EpicsSignal, ':CURSTP')
    play_count = Cpt(EpicsSignal, ':PLYCNT')
    play_status = Cpt(EpicsSignalRO, ':PLSTAT', auto_monitor=True)
    play_mode = Cpt(EpicsSignal, ':PLYMOD')

    _default_read_attrs = ['play_status']
    _default_configuration_attrs = ['play_mode', 'sequence_length']

    def __init__(self, prefix, *, name=None,  **kwargs):
        # Device initialization
        super().__init__(prefix, name=name, **kwargs)
        # Data caches
        self._steps = list()
        self._iterations = list()

    @raise_if_disconnected
    def kickoff(self):
        """
        Start the EventSequencer

        Returns
        -------
        status : SubscriptionStatus
            Status indicating whether or not the EventSequencer has started
        """
        # Clear cached data from prior runs
        self._steps.clear()
        self._iterations.clear()
        # Start the sequencer
        self.play_control.set(1)

        # Subscribe to changes in the play step and iteration
        def add_event(cache, timestamp=None, value=None, **kwargs):
            cache.append((timestamp, value))

        self.current_step.subscribe(partial(add_event, self._steps))
        self.play_count.subscribe(partial(add_event, self._iterations))

        # Create our status
        def done(*args, value=None, old_value=None, **kwargs):
            return value == 2 and old_value == 0
        # Create our status object
        return SubscriptionStatus(self.play_status, done, run=True)

    def complete(self):
        """
        Complete the EventSequencer's current sequence

        The result of this method varies on the mode that the EventSequencer is
        configured. If the EventSequencer is either set to "Run Once" or "Run N
        Times" this method allows the current sequence to complete and returns
        a status object that indicates a successful completion. However, this
        mode of operation does not make sense if the EventSequencer is in
        "Run Forever" mode. In this case, the EventSequencer is stopped
        immediately and a completed status object is returned.

        Returns
        -------
        status: DeviceStatus or SubscriptionStatus
            Status indicating completion of sequence

        Note
        ----
        If you want to stop the sequence from running regardless of
        configuration use the :meth:`.stop` command.

        """
        # Clear subscriptions
        def clear_subs(**kwargs):
            self.current_step.unsubscribe_all()
            self.play_count.unsubscribe_all()

        # If we are running forever we can stop whenever
        if self.play_mode.get() == 2:
            self.stop()
            clear_subs()
            return DeviceStatus(self, done=True, success=True)

        # Otherwise we should wait for the sequencer to end
        def done(*args, value=None, old_value=None, **kwargs):
            return value == 0 and old_value == 2

        # Create a SubscriptionStatus
        st = SubscriptionStatus(self.play_status, done, run=True)
        st.add_callback(clear_subs)
        return st

    def collect(self):
        """
        Gather information about the state of the Sequencer

        During :meth:`.kickoff`, a monitor is started on the ``current_step``
        and ``play_count`` signals. The timestamps and values of these signals
        are stored internally and can be added back into the data stream
        asynchronously by calling this method.
        """
        # Create partial event document
        event = {'time': time.time(), 'timestamps': dict(), 'data': dict()}
        for sig, cache in zip((self.current_step, self.play_count),
                              (self._steps, self._iterations)):
            event['timestamps'][sig.name] = [evt[0] for evt in cache]
            event['data'][sig.name] = [evt[1] for evt in cache]
        # Clear caches
        self._steps.clear()
        self._iterations.clear()
        yield event

    def describe_collect(self):
        """Describe the collection information"""
        dd = dict()
        dd.update(self.play_count.describe())
        dd.update(self.current_step.describe())
        return {'sequence': dd}

    def stop(self):
        """Stop the EventSequencer"""
        self.play_control.put(0)
