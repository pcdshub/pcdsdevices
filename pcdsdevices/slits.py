#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import numpy as np
from ophyd.status import wait as status_wait
from ophyd.pv_positioner import PVPositioner
from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)

logger = logging.getLogger(__name__)


class SlitPositioner(PVPositioner, Device):
    """
    PVPositioner subclass for the slit center and width pseudomotors.
    """
    setpoint = FC(EpicsSignal, "{self.prefix}:{self._dirshort}_REQ")
    readback = FC(EpicsSignalRO, "{self.prefix}:ACTUAL_{self._dirlong}")
    done = C(EpicsSignalRO, ":DMOV")

    def __init__(self, prefix="", *, slit_type="", limits=None, name=None,
                 read_attrs=None, parent=None, egu="", **kwargs):
        if parent is not None:
            prefix = parent.prefix + prefix
        self._dirlong = slit_type
        self._dirshort = slit_type[:4]
        if read_attrs is None:
            read_attrs = ["readback"]
        super().__init__(prefix, limits=limits, name=name,
                         read_attrs=read_attrs, parent=parent, egu=egu,
                         **kwargs)

    def _setup_move(self, position):
        logger.debug('%s.setpoint = %s', self.name, position)
        self.setpoint.put(position, wait=False)


class Slits(Device):
    """
    Beam slits with combined motion for center and width.

    Parameters
    ----------
    prefix : str
        The EPICS base of the motor

    name : str, optional
        The name of the offset mirror

    nominal_aperature : float, optional
        Nominal slit size that will encompass the beam without blocking

    Notes
    -----
    The slits represent a unique device when forming the lightpath as whether
    the beam is being blocked or not depends on the pointing. In order to
    create an estimate that will warn operators of narrowly closed slits while
    still allowing slits to be closed along the beampath.

    The simplest solution was to use a :attr:`.nominal_aperature` that stores
    the slit width and height that the slits should use for general operation.
    Using this the :attr:`.transmission` is calculated based on how the current
    aperature compares to the nominal, always using the minimum of the width or
    height. This means that if you have a nominal aperature of 2 mm, but your
    slits are set to 0.5 mm, the total estimated transmission will be 25%.
    Obviously this is greatly oversimplified, but it allows the lightpath to
    make a rough back of the hand calculation without being over aggressive
    about changing slit widths during alignment
    """
    xcenter = C(SlitPositioner, slit_type="XCENTER", egu="mm")
    xwidth = C(SlitPositioner, slit_type="XWIDTH", egu="mm")
    ycenter = C(SlitPositioner, slit_type="YCENTER", egu="mm")
    ywidth = C(SlitPositioner, slit_type="YWIDTH", egu="mm")
    blocked = C(EpicsSignalRO, ":BLOCKED")
    open_cmd = C(EpicsSignal, ":OPEN")
    close_cmd = C(EpicsSignal, ":CLOSE")
    block_cmd = C(EpicsSignal, ":BLOCK")

    # Subscription information
    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE

    # Default Attributes
    _default_read_attrs = ['xwidth', 'ywidth']
    _default_configuration_attrs = ['xcenter', 'ycenter']

    def __init__(self, *args, nominal_aperature=(5.0, 5.0), **kwargs):
        self._has_subscribed = False
        self.nominal_aperature = nominal_aperature
        super().__init__(*args, **kwargs)

    def move(self, size, wait=False, moved_cb=None, timeout=None):
        """
        Set the dimensions of the width/height of the gap to width paramater.

        Parameters
        ---------
        size : float, tuple
            Target size for slits in both x and y axis. Either specify as a
            tuple for a rectangular aperature (width, height) or set both with
            single floating point value

        wait : bool
            If true, block until move is completed


        timeout: float, optional
            Maximum time for the motion. If None is given, the default value of
            `xwidth` and `ywidth` positioners is used.

        moved_cb: callable, optional
            Function to be run when the operation finishes. This callback
            should not expect any arguments or keywords

        Returns
        -------
        status : AndStatus
            Logical combination of the request to both horizontal and vertical
            motors
        """
        # Check for rectangular setpoint
        if isinstance(size, tuple):
            (width, height) = size
        else:
            width, height = size, size

        # Instruct both width and height then combine the output status
        x_stat = self.xwidth.move(width, wait=False, timeout=timeout)
        y_stat = self.ywidth.move(height, wait=False, timeout=timeout)
        status = x_stat & y_stat

        # Add our callback if one was given
        if moved_cb is not None:
            status.add_callback(moved_cb)

        # Wait if instructed to do so. Stop the motors if interrupted
        if wait:
            try:
                status_wait(status)
            except KeyboardInterrupt:
                self.xwidth.stop()
                self.ywidth.stop()
                raise

        return status

    @property
    def inserted(self):
        """
        Whether the slits are inserted into the beampath
        """
        return all([self.nominal_aperature[idx] > self.current_aperature[idx]
                    for idx in range(0, 2)])

    @property
    def removed(self):
        """
        Whether the slits are entirely removed from the beampath
        """
        return not self.inserted

    @property
    def transmission(self):
        """
        Estimated transmission of the slits based on :attr:`.nominal_aperature`
        """
        # Find most restrictive side of slit aperature
        min_dim = np.argmin(self.current_aperature)
        # Don't allow transmissions over 1.0
        return min([self.current_aperature[min_dim]
                    / self.nominal_aperature[min_dim],
                    1.0])

    @property
    def current_aperature(self):
        """
        Current size of the aperature (width, height)
        """
        return (self.xwidth.position, self.ywidth.position)

    def remove(self, size=None, wait=False, timeout=None, **kwargs):
        """
        Open the slits to unblock the beam

        Parameters
        ----------
        size : float, optional
            Open the slits to a specific size otherwise
            `:attr:`.nominal_aperature is used

        wait : bool, optional
            Wait for the status object to complete the move before returning

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used

        Returns
        -------
        MoveStatus:
            Status object based on move completion

        See Also
        --------
        :meth:`Slits.move`
        """
        # Use nominal_aperature by default
        size = size or self.nominal_aperature
        return self.move(size, wait=wait, timeout=timeout, **kwargs)

    def set(self, size):
        """
        Alias for the move method, here for bluesky compatibilty
        """
        return self.move(size, wait=False)

    def open(self):
        """
        Open the slits to :attr:`.nominal_aperature` on each side
        """
        self.open_cmd.put(1)

    def close(self):
        """
        Close the slits to have an aperature of 0mm on each side
        """
        self.close_cmd.put(1)

    def block(self):
        """
        Overlap the slits to block the beam
        """
        self.block_cmd.put(1)

    def stage(self):
        """
        Store the initial values of the aperature position before scanning
        """
        self._original_vals[self.xwidth.setpoint] = self.xwidth.readback.value
        self._original_vals[self.ywidth.setpoint] = self.ywidth.readback.value
        return super().stage()

    def subscribe(self, cb, event_type=None, run=True):
        """
        Subscribe to changes of the slits

        Parameters
        ----------
        cb : callable
            Callback to be run

        event_type : str, optional
            Type of event to run callback on

        run : bool, optional
            Run the callback immediatelly
        """
        # Avoid making child subscriptions unless a client cares
        if not self._has_subscribed:
            # Subscribe to changes in aperature
            self.xwidth.readback.subscribe(self._aperature_changed,
                                           run=False)
            self.ywidth.readback.subscribe(self._aperature_changed,
                                           run=False)
            self._has_subscribed = True
        super().subscribe(cb, event_type=event_type, run=run)

    def _aperature_changed(self, *args, **kwargs):
        """
        Callback run when slit size is adjusted
        """
        # Avoid duplicate keywords
        kwargs.pop('sub_type', None)
        kwargs.pop('obj',      None)
        # Run subscriptions
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)
