#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import functools
import threading
import copy
import enum
import logging

from ophyd.status import Status
from ophyd.flyers import FlyerInterface

logger = logging.getLogger(__name__)

try:
    import pydaq
except:
    logger.warning('pydaq not in environment. Will not be able to use DAQ!')

try:
    from bluesky import RunEngine
    from bluesky.plans import run_wrapper, fly_during_wrapper
    has_bluesky = True
except ImportError:
    has_bluesky = False
    logger.warning(('bluesky not in environment. Will not have '
                    'make_daq_run_engine.'))


# Wrapper to make sure we're connected
def check_connect(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        logger.debug('Checking for daq connection')
        if not self.connected:
            msg = 'DAQ is not connected. Attempting to connect...'
            logger.info(msg)
            self.connect()
        if self.connected:
            logger.debug('Daq is connected')
            return f(self, *args, **kwargs)
        else:
            err = 'Could not connect to DAQ'
            logger.error(err)
            raise RuntimeError(err)
    return wrapper


class Daq(FlyerInterface):
    """
    The LCLS1 DAQ as a flyer object. This uses the pydaq module to connect with
    a running daq instance, controlling it via socket commands. It can be used
    as a flyer in a bluesky plan to have the daq start at the beginning of the
    run and end at the end of the run. It has additional knobs for pausing
    and resuming acquisition if desired.

    Unlike a normal bluesky flyer, this has no data to report to the RunEngine
    on the collect call. No data will pass into the python layer from the daq.
    """
    state_enum = enum.Enum('pydaq state',
                           'Disconnected Connected Configured Open Running',
                           start=0)
    default_config = dict(events=None,
                          duration=None,
                          use_l3t=False,
                          record=False,
                          controls=None)

    def __init__(self, name=None, platform=0, parent=None):
        super().__init__()
        self.name = name or 'daq'
        self.parent = parent
        self.control = None
        self.config = None
        self._host = os.uname()[1]
        self._plat = platform

    # Convenience properties
    @property
    def connected(self):
        return self.control is not None

    @property
    def configured(self):
        return self.config is not None

    @property
    def state(self):
        if self.connected:
            num = self.control.state()
            return self.state_enum(num).name
        else:
            return 'Disconnected'

    # Interactive methods
    def connect(self):
        """
        Connect to the DAQ instance, giving full control to the Python process.
        """
        logger.debug('Daq.connect()')
        if self.control is None:
            try:
                self.control = pydaq.Control(self._host, platform=self._plat)
                self.control.connect()
                msg = 'Connected to DAQ'
            except:
                del self.control
                self.control = None
                msg = ('Failed to connect to DAQ - check that it is up and '
                       'allocated.')
        else:
            msg = 'Connect requested, but already connected to DAQ'
        logger.info(msg)

    def disconnect(self):
        """
        Disconnect from the DAQ instance, giving control back to the GUI
        """
        logger.debug('Daq.disconnect()')
        if self.control is not None:
            self.control.disconnect()
        del self.control
        self.control = None
        self.config = None
        logger.info('DAQ is disconnected.')

    @check_connect
    def wait(self, timeout=None):
        """
        Pause the thread until the DAQ is done aquiring.

        Parameters
        ----------
        timeout: float
            Maximum time to wait in seconds.
        """
        logger.debug('Daq.wait()')
        if self.state == 'Running':
            status = self._get_end_status()
            status.wait(timeout=timeout)

    def begin(self, events=None, duration=None, use_l3t=None, controls=None,
              wait=False):
        """
        Start the daq with the current configuration. Block until
        the daq has begun acquiring data. Optionally block until the daq has
        finished aquiring data.

        Parameters
        ----------
        events: int, optional
            Number events to stop acquisition at.

        duration: int, optional
            Time to run the daq in seconds.

        wait: bool, optional
            If switched to True, wait for the daq to finish aquiring data.
        """
        logger.debug('Daq.begin(events=%s, duration=%s, wait=%s)',
                     events, duration, wait)
        begin_status = self.kickoff(events=events, duration=duration,
                                    use_l3t=use_l3t, controls=controls)
        begin_status.wait()
        if wait:
            self.wait()

    @check_connect
    def stop(self):
        """
        Stop the current acquisition, ending it early.
        """
        logger.debug('Daq.stop()')
        self.control.stop()

    @check_connect
    def end_run(self):
        """
        Stop the daq if it's running, then mark the run as finished.
        """
        logger.debug('Daq.end_run()')
        self.stop()
        self.control.endrun()

    # Flyer interface
    @check_connect
    def kickoff(self, events=None, duration=None, use_l3t=None, controls=None):
        """
        Begin acquisition. This method is non-blocking.

        Returns
        -------
        ready_status: DaqStatus
            Status that will be marked as 'done' when the daq has begun to
            record data.
        """
        logger.debug('Daq.kickoff()')

        if not self.configured:
            self.configure()

        def start_thread(control, status, events, duration, use_l3t, controls):
            begin_args = self._begin_args(events, duration, use_l3t, controls)
            control.begin(**begin_args)
            status._finished(success=True)
            logger.debug('Marked kickoff as complete')

        begin_status = DaqStatus(obj=self)
        watcher = threading.Thread(target=start_thread,
                                   args=(self.control, begin_status, events,
                                         duration, use_l3t, controls))
        watcher.start()
        return begin_status

    def complete(self):
        """
        End the current run.

        Return a status object that will be marked as 'done' when the DAQ has
        finished acquiring.

        Returns
        -------
        end_status: DaqStatus
        """
        logger.debug('Daq.complete()')
        end_status = self._get_end_status()
        self.end_run()
        return end_status

    def _get_end_status(self):
        """
        Return a status object that will be marked as 'done' when the DAQ has
        finished acquiring.

        Returns
        -------
        end_status: DaqStatus
        """
        logger.debug('Daq._get_end_status()')

        def finish_thread(control, status):
            control.end()
            status._finished(success=True)
            logger.debug('Marked acquisition as complete')
        end_status = DaqStatus(obj=self)
        watcher = threading.Thread(target=finish_thread,
                                   args=(self.control, end_status))
        watcher.start()
        return end_status

    def collect(self):
        """
        As per the bluesky interface, this is a generator that is expected to
        output partial event documents. However, since we don't have any events
        to report to python, this will be a generator that immediately ends.
        """
        logger.debug('Daq.collect()')
        return
        yield

    def describe_collect(self):
        """
        As per the bluesky interface, this is how you interpret the null data
        from collect. There isn't anything here, as nothing will be collected.
        """
        logger.debug('Daq.describe_configuration()')
        return {}

    @check_connect
    def configure(self, events=None, duration=None, record=False,
                  use_l3t=False, controls=None):
        """
        Changes the daq's configuration for the next run.

        Parameters
        ----------
        events: int, optional
            If provided, the daq will run for this many events before
            stopping, unless we override in begin.
            If not provided, we'll use the duration argument instead.

        duration: int, optional
            If provided, the daq will run for this many seconds before
            stopping, unless we override in begin.
            If not provided, and events was also not provided, an empty call to
            begin() will run indefinitely.

        use_l3t: bool, optional
            If True, an events argument to begin will be reinterpreted to only
            count events that pass the level 3 trigger.

        record: bool, optional
            If True, we'll record the data. Otherwise, we'll run without
            recording.

        controls: list of tuple(str, value), optional
            If provided, these will make it into the data stream as control
            variables.

        Returns
        -------
        old, new: tuple of dict
        """
        logger.debug(('Daq.configure(events=%s, duration=%s, record=%s, '
                      'use_l3t=%s, controls=%s)'),
                     events, duration, record, use_l3t, controls)
        old = self.read_configuration()
        config_args = self._config_args(record, use_l3t, controls)
        try:
            logger.debug('Calling Control.configure with kwargs %s',
                         config_args)
            self.control.configure(**config_args)
            # self.config should reflect exactly the arguments to configure,
            # this is different than the arguments that pydaq.Control expects
            self.config = dict(events=events, duration=duration,
                               record=record, use_l3t=use_l3t,
                               controls=controls)
            msg = 'Daq configured'
            logger.info(msg)
        except:
            self.config = None
            msg = 'Failed to configure!'
            logger.exception(msg)
        new = self.read_configuration()
        return old, new

    def _config_args(self, record, use_l3t, controls):
        """
        For a given set of arguments to configure, return the arguments that
        should be sent to control.configure.

        Returns
        -------
        config_args: dict
        """
        logger.debug('Daq._config_args(%s, %s, %s)',
                     record, use_l3t, controls)
        config_args = {}
        for key, val in zip(('record', 'controls'),
                            (record, controls)):
            if val is None:
                if self.config is None:
                    config_args[key] = self.default_config[key]
                else:
                    config_args[key] = self.config[key]
            else:
                config_args[key] = val
        if use_l3t:
            config_args['l3t_events'] = 0
        else:
            config_args['events'] = 0
            for key, value in list(config_args.items()):
                if value is None:
                    del config_args[key]
        return config_args

    def _begin_args(self, events, duration, use_l3t, controls):
        """
        For a given set of arguments to begin, return the arguments that should
        be sent to control.begin

        Returns
        -------
        begin_args: dict
        """
        logger.debug('Daq._begin_args(%s, %s, %s, %s)',
                     events, duration, use_l3t, controls)
        begin_args = {}
        if events is None and duration is None:
            config = self.read_configuration()
            events = config['events']
            duration = config['duration']
        if events is not None:
            if use_l3t is None and self.config is not None:
                use_l3t = self.config['use_l3t']
            if use_l3t:
                begin_args['l3t_events'] = events
            else:
                begin_args['events'] = events
        elif duration is not None:
            begin_args['duration'] = duration
        else:
            begin_args['events'] = 0  # Run until manual stop
        if controls is not None:
            begin_args['controls'] = controls
        return begin_args

    def read_configuration(self):
        """
        Returns
        -------
        config: dict
            Mapping of config key to current configured value.
        """
        logger.debug('Daq.read_configuration()')
        if self.config is None:
            config = self.default_config
        else:
            config = self.config
        return copy.deepcopy(config)

    def describe_configuration(self):
        """
        Returns
        -------
        config_desc: dict
            Mapping of config key to field metadata.
        """
        logger.debug('Daq.describe_configuration()')
        try:
            config = self.read_configuration()
            controls_shape = [len(config['control']), 2]
        except (RuntimeError, AttributeError):
            controls_shape = None
        return dict(events=dict(source='daq_events_in_run',
                                dtype='number',
                                shape=None),
                    duration=dict(source='daq_run_duration',
                                  dtype='number',
                                  shape=None),
                    use_l3t=dict(source='daq_use_l3trigger',
                                 dtype='number',
                                 shape=None),
                    record=dict(source='daq_record_run',
                                dtype='number',
                                shape=None),
                    controls=dict(source='daq_control_vars',
                                  dtype='array',
                                  shape=controls_shape))

    def stage(self):
        """
        Nothing to be done here, but we overwrite the default stage because it
        is expecting sub devices.

        Returns
        -------
        staged: list
            list of devices staged
        """
        logger.debug('Daq.stage()')
        return [self]

    def unstage(self):
        """
        Nothing to be done here, but we overwrite the default stage because it
        is expecting sub devices.

        Returns
        -------
        unstaged: list
            list of devices unstaged
        """
        logger.debug('Daq.unstage()')
        return [self]

    def pause(self):
        """
        Stop acquiring data, but don't end the run.
        """
        logger.debug('Daq.pause()')
        if self.state == 'Running':
            self.stop()

    def resume(self):
        """
        Continue acquiring data in a previously paused run.
        """
        logger.debug('Daq.resume()')
        if self.state == 'Open':
            self.begin()

    def __del__(self):
        if self.state in ('Open', 'Running'):
            self.end_run()
        self.disconnect()


class DaqStatus(Status):
    """
    Extend status to add a convenient wait function.
    """
    def wait(self, timeout=None):
        self._wait_done = threading.Event()

        def cb(*args, **kwargs):
            self._wait_done.set()
        self.finished_cb = cb
        self._wait_done.wait(timeout=timeout)


if has_bluesky:
    def make_daq_run_engine(daq):
        """
        Given a daq object, create a RunEngine that will open a run and start
        the daq for each plan.
        """
        daq_wrapper = functools.partial(fly_during_wrapper, flyers=[daq])
        RE = RunEngine(preprocessors=[run_wrapper, daq_wrapper])
        return RE
