#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standard classes for valves used throughout LCLS.
"""

############
# Standard #
############
import logging
from enum import Enum
from copy import deepcopy

###############
# Third Party #
###############
from ophyd.positioner import PositionerBase
from ophyd.status import wait as status_wait
from ophyd.utils.epics_pvs import raise_if_disconnected

##########
# Module #
##########
from .device import Device
from .state import pvstate_class
from .iocdevice import IocDevice
from .signal import EpicsSignalRO
from .signal import EpicsSignal
from .component import (Component, FormattedComponent)
from .iocadmin import IocAdminOld

logger = logging.getLogger(__name__)

ValveLimits = pvstate_class('ValveLimits',
                            {'open_limit': {'pvname': ':OPN_DI',
                                            0: 'defer',
                                            1: 'out'},
                             'closed_limit': {'pvname': ':CLS_DI',
                                              0: 'defer',
                                              1: 'in'}},
                            doc='State description of valve limits')


class Commands(Enum):
    """
    Command aliases for ``OPN_SW``
    """
    close_valve = 0
    open_valve = 1


class InterlockError(Exception):
    """
    Error when request is blocked by interlock logic
    """
    pass


class ValveBase(Device):
    """
    Base Vacuum Valve Class

    This class implements functionality common to all valves at LCLS which are
    the ability to open/close and read an interlock. All other valves should
    inherit from this class when adding additional features.

    Components
    ----------
    command : EpicsSignal, ":OPN_SWMON"/"OPN_SW"
        Signal to PV that sends move commands.

    interlock : EpicsSignalRO, ":ILKSTATUS"
        Readback for interlock PV of the valve.

    Attributes
    ----------
    commands : Enum
        Command aliases for valve.
    """
    command = FormattedComponent(EpicsSignal, "{self._prefix}:OPN_DO",
                                 write_pv="{self._prefix}:OPN_SW")
    interlock = Component(EpicsSignalRO, ":ILKSTATUS")
    limits = Component(ValveLimits, "")
    commands = Commands

    def __init__(self, prefix, *, name=None, read_attrs=None, **kwargs):
        self._prefix = prefix
        # Configure read attributes
        if read_attrs is None:
            read_attrs = ["interlock", "command", "limits"]

        super().__init__(prefix, read_attrs=read_attrs, name=name, **kwargs)
        
    @raise_if_disconnected
    def move(self, position, wait=True, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete. Valves can only be set to an open or closed position. Valid
        inputs for the 'position' argument are 'open', 'close', 1, and 0.
        String inputs are not case-sensitive.

        Parameters
        ----------
        position : str or int
            Position to move to.

        wait : bool, optional
            Wait for the status object to complete the move before returning.

        Returns
        -------
        status : MoveStatus
            Status object of the move.

        Raises
        ------
        ValueError
            On invalid positions.

        RuntimeError
            If motion fails other than timing out.
        """
        # Begin the move process
        self.check_value(position)
        logger.debug("Moving {} to {}".format(self.name, position))

        # Close the valve
        if position == 0 or isinstance(position, str) and \
          position.lower() == "close":
            status = self.command.set(self.commands.close_valve.value)
        # Open the valve
        if position == 1 or isinstance(position, str) and \
          position.lower() == "open":
            status = self.command.set(self.commands.open_valve.value)

        # Wait for the status object to register the move as complete
        if wait:
            logger.info("Waiting for {} to finish move ...".format(self.name))
            status_wait(status)
        
        return status

    def mv(self, position, **kwargs):
        """
        Alias for the move() method.
        
        Returns
        -------
        status : MoveStatus
            Status object of the move.
        """
        return self.move(position, **kwargs)

    def set(self, position, **kwargs):
        """
        Alias for the move() method.
        
        Returns
        -------
        status : MoveStatus
            Status object of the move.
        """
        return self.move(position, **kwargs)

    def open(self, **kwargs):
        """
        Remove the valve from the beam. Alias for self.move("OPEN").

        Returns
        -------
        status : MoveStatus
            Status object of the move
        """
        return self.move("OPEN", **kwargs)

    def close(self, **kwargs):
        """
        Close the valve. Alias for self.move("CLOSE")

        Returns
        -------
        status : MoveStatus
            Status object of the move
        """
        return self.move("CLOSE", **kwargs)

    def check_value(self, value):
        """
        Checks to see if the requested position is valid. This is run within
        PositionerBase.move()

        Parameters
        ----------
        value : str or int
            Position to check before a move.
        
        Raises
        ------
        ValueError
            Invalid entry for move is inputted.
        
        InterlockError
            If an open move is requested but the interlock does not permit it.
        """
        # Check for invalid moves
        if not isinstance(value, bool) and value in [0, 1] or isinstance(
                value, str) and value.lower() in ["open", "close"]:
            pass
        else:
            err_str = "Invalid move entry '{0}', must be 'close' / 'open' or " \
              "'0' / '1'.".format(value)
            logger.error(err_str)
            raise ValueError(err_str)

        # Check for interlock issues
        if value == 1 or isinstance(value, str) and value.lower() == "open":
            if self.interlocked:
                raise InterlockError("Valve is currently forced closed")

    @property
    @raise_if_disconnected
    def interlocked(self):
        """
        Whether the interlock on the valve is active, preventing the valve from
        opening.

        Returns
        -------
        interlock : bool
        	Whether the valve is currently interlocked
        """
        return bool(self.interlock.value)


class PositionValve(ValveBase):
    """
    Base valve that has the position PV.
    
    Components
    ----------
    pos : EpicsSignalRO, ":POSITION"
        Readback for the current position of the valve.
    """
    pos = Component(EpicsSignalRO, ":POSITION")

    def __init__(self, prefix, *, read_attrs=None, **kwargs):

        # Configure read attributes
        if read_attrs is None:
            read_attrs = ["interlock", "pos", "limits"]

        super().__init__(prefix, read_attrs=read_attrs, **kwargs)

    @property
    @raise_if_disconnected
    def position(self):
        """
        Read back for the position of the valve.
        """
        return self.pos.value


class BypassValve(ValveBase):
    """
    Base valve that has a bypass PV.

    Components
    ----------
    bypass_mode : EpicsSignal, ":BYPASS"
        Signal to control and read back bypass mode of the valve.
    """
    bypass_mode = Component(EpicsSignal, ":BYPASS")

    def __init__(self, prefix, *, read_attrs=None, **kwargs):
        # Configure read attributes
        if read_attrs is None:
            read_attrs = ["interlock", "command", "limits", "bypass_mode"]

        super().__init__(prefix, read_attrs=read_attrs, **kwargs)

        # Warn the user if the valve is in bypass mode
        if self.bypass is True:
            logger.warning("Valve '{0}' is currently in bypass mode".format(
                self.name))

    @property
    @raise_if_disconnected
    def bypass(self):
        """
        Returns whether the valve is currently in bypass mode.

        Returns
        -------
        bypass : bool
            Whether the valve is currently in bypass mode.
        """
        return bool(self.bypass_mode.value)

    @bypass.setter
    def bypass(self, mode):
        """
        Sets bypass mode of the valve.

        Returns
        -------
        status : Status
            Status object from the set() method.
        """
        if bool(mode) is True:
            logger.warning("Setting valve '{0}' to bypass mode.".format(
                self.name))
            return self.bypass_mode.put(1)
        else:
            return self.bypass_mode.put(0)

class OverrideValve(ValveBase):
    """
    Base class that has the override PV.

    Components
    ----------
    override_mode : EpicsSignal, ":OVERRIDE"
        Signal to control and read back override mode of the valve.
    """
    override_mode = Component(EpicsSignal, ":OVERRIDE")

    def __init__(self, prefix, *, read_attrs=None, **kwargs):
        # Configure read attributes
        if read_attrs is None:
            read_attrs = ["interlock", "command", "limits", "override_mode"]

        super().__init__(prefix, read_attrs=read_attrs, **kwargs)

        # Warn the user if the valve is in override mode
        if self.override is True:
            logger.warning("Valve '{0}' is currently in override mode".format(
                self.name))

    @property
    @raise_if_disconnected
    def override(self):
        """
        Returns whether the valve is currently in override mode.

        Returns
        -------
        override : bool
            Whether the valve is currently in override mode.
        """
        return bool(self.override_mode.value)

    @override.setter
    def override(self, mode):
        """
        Sets override mode of the valve.

        Returns
        -------
        status : Status
            Status object from the set() method.
        """
        if bool(mode) is True:
            logger.warning("Setting valve '{0}' to override mode.".format(
                self.name))
            return self.override_mode.set(1)
        else:
            return self.override_mode.set(0)


# Various High Level Valve Classes


class N2CutoffValve(OverrideValve):
    """
    Valve used to separate the nitrogen supply from the rest of the system.
    """
    pass


class ApertureValve(PositionValve, BypassValve):
    """
    Aperture valves that have both a position PV and a bypass PV.
    """
    def __init__(self, prefix, *, read_attrs=None, **kwargs):

        # Configure read attributes
        if read_attrs is None:
            read_attrs = ["interlock", "pos", "bypass_mode", "limits"]
        super().__init__(prefix, read_attrs=read_attrs, **kwargs)


class ReadbackValve(PositionValve, OverrideValve):
    """
    Valves that have the position PV and the override PV.
    """
    def __init__(self, prefix, *, read_attrs=None, **kwargs):

        # Configure read attributes
        if read_attrs is None:
            read_attrs = ["interlock", "pos", "override_mode", "limits"]
        super().__init__(prefix, read_attrs=read_attrs, **kwargs)


class GateValve(ValveBase, IocDevice):
    ioc = deepcopy(IocDevice.ioc)
    ioc.cls = IocAdminOld

    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, ioc=ioc, **kwargs)
