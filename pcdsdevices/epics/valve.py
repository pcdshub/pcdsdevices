#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standard classes for LCLS Gate Valves
"""
import logging
from enum import Enum
from copy import deepcopy
from functools import partial

from .mps import MPS, mps_factory
from .state import pvstate_class, StateStatus
from .device import Device
from .signal import EpicsSignalRO
from .signal import EpicsSignal
from .component import Component as C
from .component import FormattedComponent as FC
from .iocadmin import IocAdminOld


logger = logging.getLogger(__name__)

class Commands(Enum):
    """
    Command aliases for opening and closing valves
    """
    close_valve = 0
    open_valve = 1


class InterlockError(PermissionError):
    """
    Error when request is blocked by interlock logic
    """
    pass


ValveLimits = pvstate_class('ValveLimits',
                            {'open_limit': {'pvname': ':OPN_DI',
                                            0: 'defer',
                                            1: 'out'},
                             'closed_limit': {'pvname': ':CLS_DI',
                                              0: 'defer',
                                              1: 'in'}},
                            doc='State description of valve limits')

StopperLimits = pvstate_class('Limits',
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
    limits = C(StopperLimits, '')

    #Information on device control
    command = C(EpicsSignal, ':CMD')
    commands = Commands

    #Subscription information
    SUB_LIMIT_CH = 'sub_limit_changed'
    _default_sub = SUB_LIMIT_CH

    def __init__(self, prefix, *, name=None,
                 read_attrs=None, **kwargs):

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
        self.command.put(self.commands.open_valve.value)
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
        self.command.put(self.commands.close_valve.value)
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



class GateValve(Stopper):
    """
    Basic Vacuum Valve

    Attributes
    ----------
    commands : Enum
        Command aliases for valve
    """
    #Limit based states
    limits    = C(ValveLimits, "")
    
    #Commands and Interlock information
    command   = C(EpicsSignal,   ':OPN_SW')
    interlock = C(EpicsSignalRO, ':OPN_OK')
    
    def __init__(self, prefix, *, name=None,
                 read_attrs=None, ioc=None,
                 **kwargs):

        # Configure read attributes
        if read_attrs is None:
            read_attrs = ['interlock', 'limits']

        super().__init__(prefix,read_attrs=read_attrs,
                         name=name, **kwargs)

    @property
    def interlocked(self):
        """
        Whether the interlock on the valve is active, preventing the valve from
        opening
        """
        return bool(self.interlock.get())


    def open(self, wait=False, timeout=None, **kwargs):
        """
        Open the valve

        Parameters
        ----------
        wait : bool, optional
            Wait for the command to finish

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Raises
        ------
        InterlockError:
            When the gate valve can not be opened due to a vacuum interlock

        Returns
        -------
        StateStatus:
            Future that reports the completion of the request
        """
        if self.interlocked:
            raise InterlockError('Valve is currently forced closed')

        return super().open(wait=wait, timeout=timeout, **kwargs)


MPSGateValve = partial(mps_factory, 'MPSGateValve', GateValve)
MPSStopper   = partial(mps_factory, 'MPSStopper', Stopper)

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

    #MPS Information
    mps = FC(MPS, '{self._mps_prefix}', veto=True)

    def __init__(self, prefix, *, name=None,
                 read_attrs=None,
                 mps_prefix=None, **kwargs):

        #Store MPS information
        self._mps_prefix = mps_prefix

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
