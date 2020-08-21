from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO

from .interface import BaseInterface
from .pv_positioner import PVPositionerIsClose
from .signal import AvgSignal


class BeamStats(Device, BaseInterface):
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


class BeamEnergyRequest(PVPositionerIsClose):
    """
    Positioner to request beam color changes from ACR in eV.

    It is up to ACR how to and whether to fulfill these requests. This is often
    fulfilled by moving the Vernier but can also be a more involved process.

    Motion is considered "done" when the photon energy readback is close enough
    to the requested value. The default tolerance here is 30 eV, but this can
    be changed on a per-instance basis by passing ``atol`` into the
    initializer, or on a per-subclass basis by overriding the default.

    Parameters
    ----------
    prefix: str
        PV prefix for the request setpoint. This should always be a hutch name.

    name: str, required keyword
        Name to use for this device in log messages, data streams, etc.

    energy_pv: str, optional
        PV to use for the beam energy readback in eV. The default is
        BLD:SYS0:500:PHOTONENERGY, same as used in the BeamStats class.

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
    readback = FCpt(EpicsSignalRO, '{energy_pv}', kind='hinted')

    def __init__(self, prefix, *, name, energy_pv='BLD:SYS0:500:PHOTONENERGY',
                 skip_small_moves=True, **kwargs):
        self.energy_pv = energy_pv
        self.skip_small_moves = skip_small_moves
        super().__init__(prefix, name=name, **kwargs)

    def _setup_move(self, position):
        """Skip the move part of the move if below the tolerance."""
        if self.skip_small_moves and abs(position-self.position) < self.atol:
            # Toggle the done bit
            self.log.debug('Skipping small move in beam energy request')
            self._update_setpoint(value=self._last_setpoint)
        else:
            # Do a move
            self.log.debug('Doing beam energy request move')
            super()._setup_move(position)
