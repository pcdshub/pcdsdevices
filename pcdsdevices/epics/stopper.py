#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generic X-Ray Stoppers
"""
import logging
from enum import Enum

from .state import pvstate_class, StateStatus
from .device import Device
from .signal import EpicsSignal
from .component import Component as C


logger = logging.getLogger(__name__)


PPS = pvstate_class('PPS',
                    {'signal': {'pvname': '',
                                 0: 'out',
                                 1: 'unknown',
                                 2: 'unknown',
                                 3: 'unknown',
                                 4: 'in'}},
                    doc='MPS Summary of Stopper state')


class PPSStopper(Device):
    """
    PPS Stopper

    Control of this device only available to PPS systems. This class merely
    interprets the summary of limit switches to let the controls system know
    the current position

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV

    name : str, optional
        Alias for the stopper
    """
    summary = C(PPS, '')
    _default_sub = PPS._default_sub

    def __init__(self, prefix, *, name=None,
                 read_attrs=None,
                 mps=None, **kwargs):

        if not read_attrs:
            read_attrs = ['summary']

        super().__init__(prefix,
                         read_attrs=read_attrs,
                         name=name, **kwargs)


    @property
    def inserted(self):
        """
        Inserted limit of PPS stopper
        """
        return self.summary.value == 'in'


    @property
    def removed(self):
        """
        Removed limit of the PPS Stopper
        """
        return self.summary.value == 'out'


    def remove(self, **kwargs):
        """
        Stopper can not be controlled via EPICS

        Raises
        ------
        PermissionError

        Notes
        -----
        Exists to satisfy `lightpath` API
        """
        raise PermissionError("PPS Stopper {} can not be commanded via EPICS"
                              "".format(self.name))


    def subscribe(self, cb, event_type=None, run=False):
        """
        Subscribe to Stopper state changes

        This simply maps to the :attr:`.summary` component

        Parameters
        ----------
        cb : callable
            Callback to be run

        event_type : str, optional
            Type of event to run callback on

        run : bool, optional
            Run the callback immediatelly
        """
        return self.summary.subscribe(cb, event_type=event_type, run=run)


class Commands(Enum):
    """
    Command aliases for Stopper ``CMD`` record
    """
    close_stopper = 0
    open_stopper  = 1


Limits = pvstate_class('Limits',
                       {'open_limit': {'pvname': ':OPEN',
                                       0: 'defer',
                                       1: 'out'},
                        'closed_limit': {'pvname': ':CLOSE',
                                         0: 'defer',
                                         1: 'in'}},
                       doc='State description of Stopper limits')


class Stopper(Device):
    """
    Controls Stopper

    Similar to the :class:`.GateValve`, the Stopper class provides basic
    support for Controls stoppers i.e stoppers that can be commanded from
    outside the PPS system

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV

    name : str, optional
        Alias for the stopper
    """
    #Limit based states
    limits = C(Limits, '')

    #Information on device control
    command = C(EpicsSignal, ':CMD')
    commands = Commands

    #Subscription information
    SUB_LIMIT_CH = 'sub_limit_changed'
    _default_sub = SUB_LIMIT_CH

    def __init__(self, prefix, *, name=None,
                 read_attrs=None,
                 mps=None, **kwargs):

        if read_attrs is None:
            read_attrs = ['limits']

        super().__init__(prefix,
                         read_attrs=read_attrs,
                         name=name, **kwargs)
        #Subscribe callback to limits
        self.limits.subscribe(self._limits_changed,
                              run=False)


    def open(self, wait=False, timeout=None):
        """
        Open the stopper
        
        Parameters
        ----------
        wait : bool, optional
            Wait for the command to finish

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Returns
        -------
        StateStatus:
            Future that reports the completion of the request
        """
        #Command the stopper
        self.command.put(self.commands.open_stopper.value)
        #Create StateStatus
        status = StateStatus(self.limits, 'out', timeout=timeout)
        #Optional wait
        if wait:
            status_wait(status)

        return status


    def close(self, wait=False, timeout=None):
        """
        Close the stopper
        
        Parameters
        ----------
        wait : bool, optional
            Wait for the command to finish

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Returns
        -------
        StateStatus:
            Future that reports the completion of the request
        """
        #Command the stopper
        self.command.put(self.commands.close_stopper.value)
        #Create StateStatus
        status = StateStatus(self.limits, 'in', timeout=timeout)
        #Optional wait
        if wait:
            status_wait(status)

        return status


    def remove(self, wait=False, timeout=None):
        """
        Remove the stopper from the beam
        
        Parameters
        ----------
        wait : bool, optional
            Wait for the command to finish

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Returns
        -------
        StateStatus:
            Future that reports the completion of the request
    
        Notes
        -----
        Satisfies lightpath API

        See Also
        --------
        :meth:`.Stopper.remove`
        """
        return self.open(wait=wait, timeout=timeout)


    @property
    def inserted(self):
        """
        Whether the stopper is in the beamline
        """
        return self.limits.value == 'in'


    @property
    def removed(self):
        """
        Whether the stopper is removed from the beamline
        """
        return self.limits.value == 'out'


    def _limits_changed(self, *args, **kwargs):
        """
        Callback when the limit state of the stopper changes
        """
        kwargs.pop('sub_type', None)
        self._run_subs(sub_type=self.SUB_LIMIT_CH, **kwargs)
