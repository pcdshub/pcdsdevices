#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import functools
import logging

from ophyd.status import StatusBase
from ophyd.flyers import FlyerInterface
import pydaq

logger = logging.getLogger(__name__)


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
    def __init__(self, name, platform=0, parent=None):
        super().__init__()
        self.name = name
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

    # Wrapper to make sure we're connected
    def check_connect(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if not self.connected:
                msg = 'DAQ is not connected. Attempting to connect...'
                logger.info(msg)
                self.connect()
            if self.connected:
                return f(self, *args, **kwargs)
            else:
                raise RuntimeError('Could not connect to DAQ.')
        return wrapper

    # Wrapper to make sure we've configured
    def check_config(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if self.configured:
                return f(self, *args, **kwargs)
            else:
                raise RuntimeError('DAQ is not configured.')
        return wrapper

    # Interactive methods
    def connect(self):
        """
        Connect to the DAQ instance, giving full control to the Python process.
        """
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
        if self.control is not None:
            self.control.disconnect()
        del self.control
        self.control = None
        self.config = None
        logger.info('DAQ is disconnected.')

    @check_connect
    def wait(self):
        """
        Pause the thread until the DAQ is done aquiring.
        """
        pass

    @check_config
    def begin(self):
        """
        Start the daq with the current configuration. Block until the daq has
        begun acquiring data.
        """
        pass

    # Utility methods
    def _end_status(self):
        """
        Return a status object that will be marked as 'done' when the DAQ has
        finished acquiring.

        Returns
        -------
        done_status: StatusBase
        """
        pass

    # Flyer interface
    @check_config
    def kickoff(self):
        """
        Begin acquisition. This method is non-blocking.

        Returns
        -------
        ready_status: StatusBase
            Status that will be marked as 'done' when the daq has begun to
            record data.
        """
        pass

    def complete(self):
        """
        Returns a status that will be marked done when acquisition has been
        completed.

        Returns
        -------
        complete_status: StatusBase
        """
        pass

    def collect(self):
        """
        As per the bluesky interface, this is a generator that is expected to
        output partial event documents. However, since we don't have any events
        to report to python, this will be a generator that immediately ends.
        """
        raise GeneratorExit

    def describe_collect(self):
        """
        As per the bluesky interface, this is how you interpret the null data
        from collect. There isn't anything here.
        """
        return {}

    @check_connect
    def configure(self, *args, **kwargs):
        """
        Changes the daq's configuration for the next run.

        Parameters
        ----------
        TODO Fill this in

        Returns
        -------
        old, new: tuple of dict
        """
        pass

    @check_config
    def read_configuration(self):
        """
        Returns
        -------
        config: dict
            Mapping of config key to current configured value.
        """
        pass

    def describe_configuration(self):
        """
        Returns
        -------
        config_desc: dict
            Mapping of config key to field metadata.
        """
        pass

    def unstage(self):
        """
        If the daq is running and the run has not ended, end it.

        Returns
        -------
        unstaged: list
            list of devices unstaged
        """
        pass

    def pause(self):
        """
        Stop acquiring data, but don't end the run.
        """
        pass

    def resume(self):
        """
        Continue acquiring data in a previously paused run.
        """
        pass
