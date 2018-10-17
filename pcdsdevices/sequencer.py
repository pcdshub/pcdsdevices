import logging

from ophyd import Device, EpicsSignal, EpicsSignalRO, Component as Cpt
from ophyd import FormattedComponent as FCpt
from ophyd.status import DeviceStatus, SubscriptionStatus
from ophyd.utils.epics_pvs import raise_if_disconnected
from ophyd.flyers import FlyerInterface, MonitorFlyerMixin

logger = logging.getLogger(__name__)


class EventSequencer(Device, MonitorFlyerMixin, FlyerInterface):
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

    Run the EventSequencer at each step in my scan after completing the
    motor move and detector reading:

    .. code::

        scan([sequencer], motor, ....)

    Note
    ----
    It is ambiguous what the correct behavior for the EventSequencer is when we
    pause and resume during a scan. The current implementation will stop the
    EventSequencer and restart the sequence from the beginning. This may impact
    applications which depend on a long single looped sequence running through
    out the scan

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

    def __init__(self, prefix, *, name=None, monitor_attrs=None, **kwargs):
        monitor_attrs = monitor_attrs or ['current_step', 'play_count']

        # Setup Event Sequence
        hutch_map = {1:'AMO', 2:'SXR', 3:'XPP', 4:'XCS', 5:'CXI', 6:'MEC', 7:'MFX', 8:'XPP', 9:'MFX', 10:'SXR', 11:'XPP', 12:'XCS', 13:None, 14:None, 15:None, 16:'CXI'}
        hutch = hutch_map[int(prefix.split(':')[-1])]
    
        self.sequence = EventSequence('{}:ECS:IOC:01'.format(hutch), hutch_num=prefix[-1], name='{}_sequence'.format(hutch))

        # Device initialization
        super().__init__(prefix, name=name,
                         monitor_attrs=monitor_attrs, **kwargs)

    @raise_if_disconnected
    def kickoff(self):
        """
        Start the EventSequencer

        Returns
        -------
        status : SubscriptionStatus
            Status indicating whether or not the EventSequencer has started
        """
        self.start()
        # Start monitor signals
        super().kickoff()

        # Create our status
        def done(*args, value=None, old_value=None, **kwargs):
            return value == 2 and old_value == 0

        # Create our status object
        return SubscriptionStatus(self.play_status, done, run=True)

    @raise_if_disconnected
    def start(self):
        """
        Start the EventSequencer
        """
        # Start the sequencer
        logger.debug("Starting EventSequencer ...")
        self.play_control.put(1)

    def trigger(self):
        """
        Trigger the EventSequencer

        This method reconfigures the EventSequencer to take a new reading. This
        means:

            * Stopping the EventSequencer if it is already running
            * Restarting the EventSequencer

        The returned status object will indicate different behavior based on
        the configuration of the EventSequencer itself. If set to "Run
        Forever", the status object merely indicates that we have succesfully
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
        def done(*args, value=None, old_value=None, **kwargs):
            return value == 2 and old_value == 0

        # Create our status object
        return SubscriptionStatus(self.play_status, done, run=True)

    def pause(self):
        """Stop the event sequencer and stop monitoring events"""
        # Order a stop
        self.stop()
        # Pause monitoring
        super().pause()

    def resume(self):
        """Resume the EventSequencer procedure"""
        super().resume()
        self.start()

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
        # Clear the monitor subscriptions
        super().complete()
        # If we are running forever we can stop whenever
        if self.play_mode.get() == 2:
            logger.debug("EventSequencer is set to run forever, "
                         "stopping immediately")
            self.stop()
            return DeviceStatus(self, done=True, success=True)

        # Otherwise we should wait for the sequencer to end
        def done(*args, value=None, old_value=None, **kwargs):
            return value == 0 and old_value == 2

        # Create a SubscriptionStatus
        logger.debug("EventSequencer has a determined stopping point, "
                     " waiting for sequence to complete")
        st = SubscriptionStatus(self.play_status, done, run=True)
        return st

    def stop(self):
        """Stop the EventSequencer"""
        logger.debug("Stopping the EventSequencer")
        self.play_control.put(0)


class SequenceLine(Device):
    """Sub-class for event sequencer line."""

    ec = FCpt(EpicsSignal, '{self.prefix}:EC_{self._ID}:{self._line}')
    bd = FCpt(EpicsSignal, '{self.prefix}:BD_{self._ID}:{self._line}')
    fd = FCpt(EpicsSignal, '{self.prefix}:FD_{self._ID}:{self._line}')
    bc = FCpt(EpicsSignal, '{self.prefix}:BC_{self._ID}:{self._line}')
    ds = FCpt(EpicsSignal, '{self.prefix}:EC_{self._ID}:{self._line}.DESC')

    def __init__(self, prefix, hutch_id=None, line=None, **kwargs):

        self._ID = hutch_id
        self._line = line

        super().__init__(prefix, **kwargs)

    def get(self):
        """Read this line of the event sequence. 

        Parameters
        ----------
        None.

        Examples
        --------
        SequenceLine.read()

        """
        event_code = self.ec.get()
        beam_delta = self.bd.get()
        fiducial_delta = self.fd.get()
        burst_count = self.bc.get()
        description = self.ds.get()
        
        line = [event_code, beam_delta, fiducial_delta, burst_count, description]

        return line

    def put(self, line):
        """Write to this line of the event sequence. 

        Parameters
        ----------
        line: list
            Four item list containing the desired values for event code,
            beam delta, fiducial delta, and burst count, respectively, e.g.
            [<event code>, <beam delta>, <fiducial delta>, <burst count>].

        Examples
        --------
        SequenceLine.write([140, 12, 0, 0, 'description'])

        """

        if len(line) != 5:
            raise ValueError("The sequence line must be a 5 item list!")
        else:
            self.ec.put(line[0])        
            self.bd.put(line[1])        
            self.fd.put(line[2])        
            self.bc.put(line[3])        
            self.ds.put(str(line[4]))        

class EventSequence():
    """Class for the event sequence of the event sequencer."""

    def __init__(self, prefix, hutch_num, **kwargs):
        
        self._hutch_num = hutch_num
      
        self._lines = [] 
        for i in range(0,20,1):
            line_num = str(i)
            # Pad 1 digit numbers with 0
            if len(line_num) == 1:
                line_num = '0' + line_num
            line = SequenceLine(prefix, hutch_id=self._hutch_num, line=line_num, name='line{}'.format(line_num))
            self._lines.append(line)

    def get(self):
        """Retrieve the current event sequence.

        Parameters
        ----------
        None.

        Examples
        --------

        EventSequence.get()
        
        """
        sequence = []
        for line in self._lines:
            seq_line = line.get()
            sequence.append(seq_line)

        return sequence

    def put(self, sequence):
        """Write a sequence to the event sequencer. Takes a list of lists,
        with each sub-list representing one line of the event sequence. 

        Parameters
        ----------
        sequence: list
            List of lists describing the event sequence. 

        Examples
        --------
        seq = [[167, 19, 0, 0, 'Description1'],
               [168,  4, 0, 0, 'Description2'],
               [182,  1, 0, 0, 'Description3'],
               [176,  0, 0, 0, 'Description4'],
               [169,  0, 0, 0, 'Description5']]

        EventSequence.write(seq)
        
        """

        if len(sequence) > 20:
            raise ValueError("The sequence length cannot be longer than 20!")
        else:
            for n, line in enumerate(sequence):
                seq_line = self._lines[n]
                seq_line.put(line)
