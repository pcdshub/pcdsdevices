from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO

from .interface import BaseInterface
from .pv_positioner import PVPositionerDone
from .signal import AvgSignal


class BeamStats(BaseInterface, Device):
    mj = Cpt(EpicsSignalRO, 'GDET:FEE1:241:ENRC', kind='hinted')
    ev = Cpt(EpicsSignalRO, 'BLD:SYS0:500:PHOTONENERGY', kind='normal')
    rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE', kind='normal')
    owner = Cpt(EpicsSignalRO, 'ECS:SYS0:0:BEAM_OWNER_ID', kind='omitted')

    mj_avg = Cpt(AvgSignal, 'mj', averages=120, kind='normal')
    mj_buffersize = Cpt(AttributeSignal, 'mj_avg.averages', kind='config')

    tab_component_names = True

    def __init__(self, prefix='', name='beam_stats', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)


class SxrGmd(Device):
    mj = Cpt(EpicsSignalRO, 'SXR:GMD:BLD:milliJoulesPerPulse', kind='hinted')

    def __init__(self, prefix='', name='sxr_gmd', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)


class BeamEnergyRequest(PVPositionerDone):
    """
    Positioner to request beam color changes from ACR in eV.

    It is up to ACR how to and whether to fulfill these requests. This is often
    fulfilled by moving the Vernier but can also be a more involved process.

    Motion is immedately considered "done", but will not execute unless the
    requested position delta is larger than the tolerance. The default
    tolerance here is 30 eV, but this can be changed on a per-instance basis
    by passing ``atol`` into the initializer, or on a per-subclass basis by
    overriding the default.

    Parameters
    ----------
    prefix: str
        PV prefix for the request setpoint. This should always be a hutch name.

    name: str, required keyword
        Name to use for this device in log messages, data streams, etc.

    skip_small_moves: bool, optional
        Defaults to True, which ignores move requests that are smaller than the
        atol factor. If False, we'll perform every requested move.
        This can be very useful for synchronized energy scans where the ACR
        side of the process can be very slow, but does not necessarily need to
        happen at every step. Rather than design complicated scan patterns, we
        can skip the small moves here and move the monochromater and beam
        request devices in parallel.

    atol: int, optional
        Absolute tolerance that determines when the move is done and when to
        skip moves using the skip_small_moves parameter.
    """

    # Default tolerance from Vernier in legacy XCS python
    atol = 30

    setpoint = Cpt(EpicsSignal, ':USER:MCC:EPHOT', kind='hinted')

    def __init__(self, prefix, *, name, skip_small_moves=True, **kwargs):
        super().__init__(prefix, name=name, skip_small_moves=skip_small_moves,
                         **kwargs)
