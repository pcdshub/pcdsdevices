import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO

from .interface import BaseInterface
from .pv_positioner import PVPositionerDone
from .signal import AvgSignal


logger = logging.getLogger(__name__)


class BeamStats(BaseInterface, Device):
    # Pulse energy (in mJ)
    mj = Cpt(EpicsSignalRO, 'GDET:FEE1:241:ENRC', kind='hinted')
    # Photon Energy (in eV)
    ev = Cpt(EpicsSignalRO, 'BLD:SYS0:500:PHOTONENERGY', kind='normal')
    # LCLSBEAM Event Rate (in Hz)
    rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE', kind='normal')
    # ECS: BEAM_OWNER ID
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

    # Default vernier tolerance
    atol = 5

    setpoint = Cpt(EpicsSignal, ':USER:MCC:EPHOT', kind='hinted')

    def __init__(self, prefix, *, name, skip_small_moves=True, atol=None,
                 **kwargs):
        if atol is not None:
            self.atol = atol
        super().__init__(prefix, name=name, skip_small_moves=skip_small_moves,
                         **kwargs)


class Lcls(BaseInterface, Device):
    '''
    LCLS LINAC STATUS
    bunch charge: 180 [pC]
    repetition rate: 120 [Hz]
    ebeam energy: 10.75 [GeV]
    Vernier energy: -35 [MeV]
    Photon Energy: 9.91 [keV]
    BC2 peak current: 3201 [A]
    electron bunch length: 23 [fs]
    Last eLoss Scan: 0.93 [mJ]
    '''
    # Bunch Charge nC: FBCK:BCI0:1:CHRG	no desc
    # Hard e-Energy GeV/c: BEND:DMPH:400:BDES - Desired B-Field
    # Soft e-Energ GeV/c: BEND:DMPS:400:BDES - Desired B-Field
    # Bunch Length fs: SIOC:SYS0:ML00:AO820 estimated FEL Pulse Duration (FWHM)

    # BC2 IPK:	 FBCK:FB04:LG01:S5DES	BC2 Current set point

    # Bunch charge (units: nC)
    bunch_charge = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO470', kind='normal')
    # also have this one  FBCK:BCI0:1:CHRG (nC)
    # estimated FEL Pulse Duration (FWHM) (units: fs)
    bunch_length = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO820', kind='normal')
    # BLEN:LI21:265:WIDTH - not found
    # Width of pulse (bunch length) Fsec

    # Peak current after BC2 (units: A)
    peak_current = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO195', kind='normal')
    # Last Eloss sxray energy (units: mJ)
    eloss_energy = Cpt(EpicsSignalRO, 'PHYS:SYS0:1:ELOSSENERGY', kind='normal')
    # Fast Feedback 6x6 Vernier (units: MeV)
    vernier_energy = Cpt(EpicsSignalRO, 'FBCK:FB04:LG01:DL2VERNIER',
                         kind='normal')

    # FBCK Vernier SIOC:SYS0:ML00:CALC209 (units: MeV)
    # DL2 Energy - FBCK:FB04:LG01:DL2VERNIER
    # Vernier Limit (% of Bend Energy):	SIOC:SYS0:ML01:AO151 Vernier Scan Range
    # Vernier Limit: SIOC:SYS0:ML01:CALC034 - Vernier Limit
    # Vernie Crtrl w/limits: SIOC:SYS0:ML01:CALC033	- Vernier Ctrl w/ limits

    # LCLSBEAM Event Rate (units: Hz)
    beam_event_rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE',
                          kind='normal')
    # Photon eV HXR (units: eV)
    photon_ev_hxr = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO627', kind='normal')

    # Abort Active Status
    # [ 0] Disable [ 1] Enable
    bykik_abort = Cpt(EpicsSignal, 'IOC:IN20:EV01:BYKIK_ABTACT', kind='normal')

    # Abort Period in  beam shots
    bykik_period = Cpt(EpicsSignal, 'IOC:IN20:EV01:BYKIK_ABTPRD',
                       kind='normal')
    # undulator k value - not the correct PV i think
    undulator_k = Cpt(EpicsSignal, 'USEG:UND1:150:KACT', kind='normal')

    def bykik_status(self):
        """
        Returns status of bykik abort
        """
        status = self.bykik_abort.get()
        if status == 0:
            return 'Disable'
        else:
            return 'Enable'

    def bykik_disable(self):
        """
        Disables bykik abort
        """
        return self.bykik_abort.put(0)

    def bykik_enable(self):
        """
        Enables bykik abort
        """
        return self.bykik_abort.put(1)

    def bykik_get_period(self):
        """
        Gets the number of events between bykik aborts
        """
        return self.bykik_period.get()

    def bykik_set_period(self, period):
        """
        Sets the number of events between bykik aborts
        """
        return self.bykik_period.put(period)

    def __init__(self, prefix='', name='lcls', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)
