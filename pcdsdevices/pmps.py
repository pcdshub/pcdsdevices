"""
Utilities related to the PMPS system.
"""
from ophyd.device import Component as Cpt

from .device import UpdateComponent as UpCpt
from .inout import TwinCATInOutPositioner
from .signal import PytmcSignal
from .state import TwinCATMalStatePositioner


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


class TwinCATMalStatePMPS(TwinCATMalStatePositioner, TwinCATStatePMPS):
    """
    Combines the ``lcls-twincat-motion-abstraction`` new-format state behavior of
    `TwinCATMalStatePositioner` (motion parameters live on the drive layer, so
    there is no per-state ``:VELO`` field or ``state_velo`` summary) with the
    PMPS protection PVs and in/out semantics of `TwinCATStatePMPS`.

    Unlike the plain `TwinCATMalStatePositioner`, this still has meaningful
    Configuration content: the ``arb_enable`` and ``maint_mode`` PMPS PVs.
    """
    config = UpCpt(state_count=2)
