import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd.flyers import FlyerInterface, MonitorFlyerMixin
from ophyd.status import DeviceStatus, SubscriptionStatus
from ophyd.utils.epics_pvs import raise_if_disconnected

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class EventSequence(BaseInterface, Device):
    """Class for the event sequence of the event sequencer."""
    ec_array = Cpt(EpicsSignal, ':SEQ.A')
    bd_array = Cpt(EpicsSignal, ':SEQ.B')
    fd_array = Cpt(EpicsSignal, ':SEQ.C')
    bc_array = Cpt(EpicsSignal, ':SEQ.D')
    seq_proc = Cpt(EpicsSignal, ':SEQ.PROC')

    tab_whitelist = ['get_seq', 'put_seq', 'show']

    def get_seq(self, current_length=True):
        """
        Retrieve the current event sequence.

        Returns a list of lists, with each sub-list containing a four item list
        describing a single line of the sequence. Returns the current sequence
        up to the current play length (the '{prefix}:LEN' PV), unless the
        `current_length` option is set to :keyword:`False`. If
        :keyword:`False`, the whole sequence will be returned.

        Parameters
        ----------
        current_length : bool
            Option to retrieve the sequence up to the current length. Defaults
            to `True`.

        Examples
        --------
        >>> EventSequence.get_seq()

        Get the whole sequence:
        >>> EventSequence.get_seq(current_length=False)
        """

        if self.parent and current_length is True:
            seq_length = self.parent.sequence_length.get()
        else:
            seq_length = 2048  # Whole thing

        sequence = [[], [], [], []]
        sequence[0] = self.ec_array.get()[0:seq_length]
        sequence[1] = self.bd_array.get()[0:seq_length]
        sequence[2] = self.fd_array.get()[0:seq_length]
        sequence[3] = self.bc_array.get()[0:seq_length]

        zip_seq = zip(sequence[0], sequence[1], sequence[2], sequence[3])
        seq_list = list(zip_seq)
        # Convert list of tuples (from zip) to list of lists
        seq = [list(line) for line in seq_list]

        return seq

    def put_seq(self, sequence, update_length=True):
        """
        Write a sequence to the event sequencer.

        Takes a list of lists, with each sub-list representing one line of the
        event sequence, e.g. ``[beam_code, delta_beam, delta_fiducial,
        burst_count]``. The written sequence will overwrite the current
        sequence in order, up to the specified length. The play length of the
        sequencer will automatically be updated, unless the `update_length`
        flag is set to :keyword:`False`.

        Parameters
        ----------
        sequence : list
            List of lists describing the event sequence. The list takes the
            form ``[[beam_code, delta_beam, delta_fiducial, burst_count],
            ...]``.

        update_length : bool
            Option to automatically update the play length (the '{prefix}:LEN'
            PV) to the length of the written sequence. Defaults to `True`.

        Examples
        --------
        >>> seq = [[182,  12,   0,   0], # Line 1
                   [170,   2,   0,   0], # Line 2
                   [169,   1,   0,   0], # Line 3
                   [169,   1,   0,   0]] # Line 4

        >>> EventSequence.put_seq(seq)

        Don't update length:
        >>> EventSequence.put_seq(seq, update_length=False)
        """

        curr_seq = self.get_seq(current_length=False)
        new_seq = curr_seq.copy()

        for i in range(len(sequence)):
            new_seq[i] = sequence[i]

        # Update the length of the sequence if update_length == True and
        # the event sequence is a child of the EventSequencer
        if self.parent and update_length is True:
            new_len = len(sequence)
            self.parent.sequence_length.put(new_len)

        seq = [arr for arr in zip(*new_seq)]
        self.ec_array.put(seq[0])
        self.bd_array.put(seq[1])
        self.fd_array.put(seq[2])
        self.bc_array.put(seq[3])
        self.seq_proc.put(1)  # Force the sequencer to update sequence

    def show(self, num_lines=None):
        """
        Print a human readable copy of the current event sequence.

        Shows the current sequence up to the length of the sequencer play
        length, unless otherwise specified by the `num_lines` parameter.

        Parameters
        ----------
        num_lines : int
            Number of event sequence lines to print. Defaults to current
            sequence length.

        Examples
        --------
        Print current sequence (default):
        >>> seq.show()

        Print the first 10 lines:
        >>> seq.show(10)
        """

        curr_seq = self.get_seq()

        for nline, line in enumerate(curr_seq):
            if nline == num_lines:
                break
            print(line)


class EventSequencer(BaseInterface, Device, MonitorFlyerMixin, FlyerInterface):
    """
    Event Sequencer.

    The LCLS Event Sequencer implemented as an Flyer; i.e. it has the methods
    :meth:`.kickoff`, :meth:`.complete` and :meth:`.collect`. This allows the
    EventSequencer to be used succinctly with the `fly_during_wrapper` and
    associated preprocessor.

    Parameters
    ----------
    prefix : str
        Base prefix of the EventSequencer.

    name : str
        Name of Event Sequencer object.

    Examples
    --------
    Run the EventSequencer throughout my scan:
    >>> fly_during_wrapper(scan([det], motor, ...), [sequencer])

    Run the EventSequencer at each step in my scan after completing the
    motor move and detector reading:
    >>> scan([sequencer], motor, ....)

    Note
    ----
    It is ambiguous what the correct behavior for the EventSequencer is when we
    pause and resume during a scan. The current implementation will stop the
    EventSequencer and restart the sequence from the beginning. This may impact
    applications which depend on a long single looped sequence running through
    out the scan.
    """

    play_control = Cpt(EpicsSignal, ':PLYCTL', kind='omitted')
    sequence_length = Cpt(EpicsSignal, ':LEN', kind='config')
    current_step = Cpt(EpicsSignal, ':CURSTP', kind='normal')
    play_count = Cpt(EpicsSignal, ':PLYCNT', kind='normal')
    total_play_count = Cpt(EpicsSignalRO, ':TPLCNT', kind='normal')
    play_status = Cpt(EpicsSignalRO, ':PLSTAT', auto_monitor=True,
                      kind='normal')
    play_mode = Cpt(EpicsSignal, ':PLYMOD', kind='config')
    sync_marker = Cpt(EpicsSignal, ':SYNCMARKER', kind='config')
    next_sync = Cpt(EpicsSignal, ':SYNCNEXTTICK', kind='config')
    pulse_req = Cpt(EpicsSignal, ':BEAMPULSEREQ', kind='config')
    rep_count = Cpt(EpicsSignal, ":REPCNT", kind='config')
    sequence_owner = Cpt(EpicsSignalRO, ':HUTCH_NAME', kind='omitted')

    sequence = Cpt(EventSequence, '', kind='config')

    tab_whitelist = ["start"]
    tab_component_names = True

    def __init__(self, prefix, *, name=None, monitor_attrs=None, **kwargs):
        monitor_attrs = monitor_attrs or ['current_step', 'play_count']

        # Device initialization
        super().__init__(prefix, name=name,
                         monitor_attrs=monitor_attrs, **kwargs)

    @raise_if_disconnected
    def kickoff(self):
        """
        Start the EventSequencer.

        Returns
        -------
        status : ~ophyd.status.SubscriptionStatus
            Status indicating whether or not the EventSequencer has started.
        """

        self.start()
        # Start monitor signals
        super().kickoff()

        # Create our status
        def done(*args, value=None, old_value=None, timestamp=0, **kwargs):
            return all((value == 2, old_value == 0,
                        timestamp > self.play_control.timestamp))

        # Create our status object
        return SubscriptionStatus(self.play_status, done, run=True)

    @raise_if_disconnected
    def start(self):
        """Start the EventSequencer."""
        # Start the sequencer
        logger.debug("Starting EventSequencer ...")
        self.play_control.put(1)

    def trigger(self):
        """
        Trigger the EventSequencer.

        This method reconfigures the EventSequencer to take a new reading. This
        means:

            * Stopping the EventSequencer if it is already running
            * Restarting the EventSequencer

        The returned status object will indicate different behavior based on
        the configuration of the EventSequencer itself. If set to 'Run
        Forever', the status object merely indicates that we have succesfully
        started our sequence. Otherwise, the status object will be completed
        when the sequence we have set it to play is complete.
        """

        # Stop the Sequencer if it is already running
        self.stop()
        # Fire the EventSequencer
        self.start()
        # If we are running forever, count this is as triggered
        if self.play_mode.get() == 2:
            logger.debug("EventSequencer is set to run forever, "
                         "trigger is complete")
            return DeviceStatus(self, done=True, success=True)

        # Create our status
        def done(*args, value=None, old_value=None, timestamp=0, **kwargs):
            return all((value == 0, old_value == 2,
                        timestamp > self.play_control.timestamp))

        # Create our status object
        return SubscriptionStatus(self.play_status, done, run=True)

    def pause(self):
        """Stop the event sequencer and stop monitoring events."""
        # Order a stop
        self.stop()
        # Pause monitoring
        super().pause()

    def resume(self):
        """Resume the EventSequencer procedure."""
        super().resume()
        self.start()

    def complete(self):
        """
        Complete the EventSequencer's current sequence.

        The result of this method varies on the mode that the EventSequencer is
        configured. If the EventSequencer is either set to 'Run Once' or 'Run N
        Times' this method allows the current sequence to complete and returns
        a status object that indicates a successful completion. However, this
        mode of operation does not make sense if the EventSequencer is in
        'Run Forever' mode. In this case, the EventSequencer is stopped
        immediately and a completed status object is returned.

        Returns
        -------
        status : DeviceStatus or SubscriptionStatus
            Status indicating completion of sequence.

        Notes
        -----
        If you want to stop the sequence from running regardless of
        configuration use the :meth:`.stop` command.
        """

        # Clear the monitor subscriptions
        super().complete()
        # If we are running forever we can stop whenever
        if self.play_mode.get() == 2:
            logger.debug("EventSequencer is set to run forever, "
                         "stopping immediately")
            self.stop()
            return DeviceStatus(self, done=True, success=True)

        # Otherwise we should wait for the sequencer to end
        def done(*args, value=None, old_value=None, timestamp=0, **kwargs):
            return all((value == 0, old_value == 2,
                        timestamp > self.play_control.timestamp))

        # Create a SubscriptionStatus
        logger.debug("EventSequencer has a determined stopping point, "
                     " waiting for sequence to complete")
        st = SubscriptionStatus(self.play_status, done, run=True)
        return st

    def stop(self):
        """Stop the EventSequencer."""
        logger.debug("Stopping the EventSequencer")
        self.play_control.put(0)
