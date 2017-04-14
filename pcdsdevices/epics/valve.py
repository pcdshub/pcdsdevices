from enum import Enum
from copy import copy

from .state import pvstate_class
from .iocdevice import IocDevice
from .signal import EpicsSignalRO
from .signal import EpicsSignal
from .component import Component
from .iocadmin import IocAdminOld


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


ValveLimits = pvstate_class('ValveLimits',
                            {'open_limit': {'pvname': ':OPN_DI',
                                            0: 'defer',
                                            1: 'out'},
                             'closed_limit': {'pvname': ':CLS_DI',
                                              0: 'defer',
                                              1: 'in'}},
                            doc='State description of valve limits')


class GateValve(IocDevice):
    """
    Basic Vacuum Valve

    Attributes
    ----------
    commands : Enum
        Command aliases for valve
    """
    ioc = copy(IocDevice.ioc)
    ioc.cls = IocAdminOld
    command = Component(EpicsSignal,   ':OPN_SW')
    interlock = Component(EpicsSignalRO, ':OPN_OK')
    limits = Component(ValveLimits, "")

    commands = Commands

    def __init__(self, prefix, *, name=None,
                 read_attrs=None, ioc=None, **kwargs):

        # Configure read attributes
        if read_attrs is None:
            read_attrs = ['interlock']

        super().__init__(prefix, ioc=ioc,
                         read_attrs=read_attrs,
                         name=name, **kwargs)

    @property
    def interlocked(self):
        """
        Whether the interlock on the valve is active, preventing the valve from
        opening
        """
        return bool(self.interlock.get())

    def open(self):
        """
        Remove the valve from the beam
        """
        if self.interlocked:
            raise InterlockError('Valve is currently forced closed')

        self.command.put(self.commands.open_valve)

    def close(self):
        """
        Close the valve
        """
        self.command.put(self.commands.close_valve)
