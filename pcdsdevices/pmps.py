"""
Utilities related to the PMPS system.
"""
from ophyd.device import Component as Cpt

from .inout import TwinCATInOutPositioner
from .signal import PytmcSignal


class TwinCATStatePMPS(TwinCATInOutPositioner):
    """
    TwinCAT In/Out State Positioner with PMPS Protections

    This class adds utility PVs for managing the PMPS state.
    """
    arb_enable = Cpt(PytmcSignal, ':PMPS:ARB:ENABLE', io='io', kind='config',
                     doc='Enables PMPS pre-emptive protections. This can be '
                         'disabled to fall back on fast-fault-only '
                         'protections. Disabling this will also clear '
                         'arbiter requests.')
    maint_mode = Cpt(PytmcSignal, ':PMPS:MAINT', io='io', kind='config',
                     doc='If this is on, we trip a fast fault and then can '
                         'move the motor freely. Useful for debugging '
                         'motion issues.')
