"""
Standard classes for LCLS Gate Valves
"""
############
# Standard #
############
from copy import copy
from enum import Enum
###############
# Third Party #
###############


##########
# Module #
##########
from .state         import pvstate_class 
from .lclsdevice    import LCLSDevice as Device
from .lclssignal    import LCLSEpicsSignalRO as EpicsSignalRO
from .lclssignal    import LCLSEpicsSignal as EpicsSignal
from .lclscomponent import LCLSComponent as C
from .lclscomponent import LCLSFormattedComponent as FC


class Commands(Enum):
    """
    Command aliases for ``OPN_SW``
    """
    close_valve = 0
    open_valve  = 1 


class InterlockError(Exception):
    """
    Error when request is blocked by interlock logic
    """
    pass

Limits = pvstate_class('Limits',
                       {'open_limit'  : {'pvname' :':OPN_DI',
                                          0       : 'defer',
                                          1       : 'out'},
                       'closed_limit' : {'pvname' :':CLS_DI',
                                          0       : 'defer',
                                          1       : 'in'}},
                       doc='State description of valve limits')


class GateValve(Device):
    """
    Basic Vacuum Valve

    Attributes
    ----------
    commands : Enum
        Command aliases for valve
    """
    command   = C(EpicsSignal,   ':OPN_SW')
    interlock = C(EpicsSignalRO, ':OPN_OK')
    limits    = C(Limits, '')

    #Command mapping 
    commands = Commands

    def __init__(self, prefix, *, name=None,
                 read_attrs=None, ioc=None,
                 mps=None, **kwargs):

        #Configure read attributes
        if read_attrs is None:
            read_attrs = ['interlock', 'limits']

        super().__init__(prefix, ioc=ioc,
                         read_attrs=read_attrs,
                         name=name)

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
