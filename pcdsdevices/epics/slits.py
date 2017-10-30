#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from ophyd.device import Staged
from ophyd.pv_positioner import PVPositioner

from .signal import EpicsSignal, EpicsSignalRO
from .component import Component, FormattedComponent
from .device import Device

logger = logging.getLogger(__name__)


class SlitPositioner(PVPositioner, Device):
    """
    PVPositioner subclass for the slit center and width pseudomotors.
    """
    setpoint = FormattedComponent(EpicsSignal,
                                  "{self.prefix}:{self._dirshort}_REQ")
    readback = FormattedComponent(EpicsSignalRO,
                                  "{self.prefix}:ACTUAL_{self._dirlong}")
    done = Component(EpicsSignalRO, ":DMOV")

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
    xcenter = Component(SlitPositioner, slit_type="XCENTER", egu="mm")
    xwidth = Component(SlitPositioner, slit_type="XWIDTH", egu="mm")
    ycenter = Component(SlitPositioner, slit_type="YCENTER", egu="mm")
    ywidth = Component(SlitPositioner, slit_type="YWIDTH", egu="mm")
    blocked = Component(EpicsSignalRO, ":BLOCKED")
    open_cmd = Component(EpicsSignal, ":OPEN")
    close_cmd = Component(EpicsSignal, ":CLOSE")
    block_cmd = Component(EpicsSignal, ":BLOCK")

    #Subscription information
    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE

    def __init__(self, prefix, *, read_attrs=None,
                 name=None, nominal_aperature=5.0, **kwargs):
        self._has_subscribed = False
        #Nominal
        self.nominal_aperature = nominal_aperature
        #Ophyd initialization
        if read_attrs is None:
            read_attrs = ['xcenter', 'xwidth', 'ycenter', 'ywidth']

        super().__init__(prefix, read_attrs=read_attrs, name=name,
                         **kwargs)


    def move(self,width,wait=False,**kwargs):
        """
        Set the dimensions of the width/height of the gap to width paramater.
        It's OK to only return one of the statuses because they share the same
        completion flag (I think).

        Parameters
        ---------
        width : float
            target width for slits in both x and y axis. EGU: mm

        wait : bool
            If true, block until move is completed

        Returns
        -------
        status : MoveStatus
            status object of the move

        """
        self.xwidth.move(width,wait=False,**kwargs)
        return self.ywidth.move(width,wait=wait,**kwargs)

    @property
    def inserted(self):
        """
        Whether the slits are inserted into the beampath
        """
        return (min(self.xwidth.position, self.ywidth.position)
                <= self.nominal_aperature)

    @property
    def removed(self):
        """
        Whether the slits are entirely removed from the beampath
        """
        return not self.inserted

    @property
    def transmission(self):
        """
        Estimated transmission of the slits based on :attr:`.nominal_aperature
        """
        #Find most restrictive side of slit aperature
        min_side = min(self.xwidth.position, self.ywidth.position)
        #Don't allow transmissions over 1.0
        return min(min_side / self.nominal_aperature, 1.0)

    def remove(self, width=None, wait=False, timeout=None, **kwargs):
        """
        Open the slits to unblock the beam

        Parameters
        ----------
        width : float, optional
            Open the slits to a specific width otherwise
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

        Raises
        ------
        ValueError:
            If the width is not greater than or equal to the
            :attr:`nominal_aperature`

        See Also
        --------
        :meth:`Slits.move`
        """
        #Use nominal_aperature by default
        width = width or self.nominal_aperature

        if width < self.nominal_aperature:
            raise ValueError("Requesed width of {} mm will still block the "
                             "beampath according to the nominal aperature "
                             "size of {} mm".format(width,
                                                    self.nominal_aperature))

        return self.move(width, wait=wait, timeout=timeout)

    def set(self,width,wait=False,**kwargs):
        """
        alias for move method 
        """
        return self.move(width,wait,**kwargs)

    def stage(self):
        """
        Record starting position of slits. This allows @stage_wrapper to make
        plans involving the slits to return to their starting positions.
        """
        self.stage_cache_xwidth = self.xwidth.position
        self.stage_cache_ywidth = self.ywidth.position
        return super().stage()

    def unstage(self):
        """
        Place slits back in their starting positions. This allows 
        @stage_wrapper to make plans involving the slits to return to their
        starting positions.
        """
        if self._staged == Staged.yes:
            self.xwidth.move(self.stage_cache_xwidth,wait=False)
            self.ywidth.move(self.stage_cache_ywidth,wait=False)
        return super().unstage()

    def open(self):
        """
        Open the slits to have a large aperature on each side
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
        if not self._has_subscribed:
            #Subscribe to changes in aperature
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
        #Avoid duplicate keywords
        kwargs.pop('sub_type', None)
        #Run subscriptions
        self._run_subs(sub_type=self.SUB_STATE, **kwargs)
