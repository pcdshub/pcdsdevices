import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO

from .interface import BaseInterface
from .pv_positioner import PVPositionerDone
from .signal import AvgSignal


logger = logging.getLogger(__name__)


class BeamStats(BaseInterface, Device):
    mj = Cpt(EpicsSignalRO, 'GDET:FEE1:241:ENRC', kind='hinted',
             doc='Pulse energy [mJ]')
    ev = Cpt(EpicsSignalRO, 'BLD:SYS0:500:PHOTONENERGY', kind='normal',
             doc='Photon Energy [eV]')
    rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE', kind='normal',
               doc='LCLSBEAM Event Rate [Hz]')
    owner = Cpt(EpicsSignalRO, 'ECS:SYS0:0:BEAM_OWNER_ID', kind='omitted',
                doc='BEAM_OWNER ID')

    mj_avg = Cpt(AvgSignal, 'mj', averages=120, kind='normal')
    mj_buffersize = Cpt(AttributeSignal, 'mj_avg.averages', kind='config')

    tab_component_names = True

    def __init__(self, prefix='', name='beam_stats', **kwargs):
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


class LCLS(BaseInterface, Device):
    """
    Object to query machine Lcls Linac status.
    """

    tab_component_names = True

    tab_whitelist = ['bykik_status', 'bykik_disable', 'bykik_enable',
                     'bykik_get_period', 'bykik_set_period']

    bunch_charge = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO470', kind='normal',
                       doc='Bunch charge [nC]')
    bunch_charge_2 = Cpt(EpicsSignalRO, 'FBCK:BCI0:1:CHRG',
                         kind='normal', doc='Bunch Charge [nC]')
    beam_event_rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE',
                          kind='normal', doc='LCLSBEAM Event Rate [Hz]')
    ebeam_energy = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO500', kind='normal',
                       doc='Final electron energy [ GeV]')
    ebeam_energy_user_req = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML01:CALC036',
                                kind='normal',
                                doc='Beam energy request from Users [GeV]')
    bunch_length = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO820', kind='normal',
                       doc='estimated FEL Pulse Duration (FWHM) [fs]')
    bc2_peak_current = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO195',
                           kind='normal', doc='Peak current after BC2 [A]')
    eloss_energy = Cpt(EpicsSignalRO, 'PHYS:SYS0:1:ELOSSENERGY', kind='normal',
                       doc='Last Eloss sxray energy [mJ]')
    vernier_energy = Cpt(EpicsSignalRO, 'FBCK:FB04:LG01:DL2VERNIER',
                         kind='normal', doc='Fast Feedback 6x6 Vernier [MeV]')
    photon_ev_hxr = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO627', kind='normal',
                        doc='Photon eV HXR [eV]')
    # [ 0] Disable [ 1] Enable
    bykik_abort = Cpt(EpicsSignal, 'IOC:IN20:EV01:BYKIK_ABTACT', kind='normal',
                      string=True, doc='BYKIK: Abort Active')
    bykik_period = Cpt(EpicsSignal, 'IOC:IN20:EV01:BYKIK_ABTPRD',
                       kind='normal', doc='BYKIK: Abort Period [beam shots]')
    undulator_k_line = Cpt(EpicsSignalRO, 'USEG:UNDS:2650:KAct', kind='normal',
                           doc='Most upstream undulator K value (K-line)')
    undulator_l_line = Cpt(EpicsSignalRO, 'USEG:UNDH:1850:KAct', kind='normal',
                           doc='Most upstream undulator K value (L-line)')
    fbck_vernier = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:CALC209', kind='normal',
                       doc='FBCK Vernier [MeV]')
    dl2_energy = Cpt(EpicsSignalRO, 'FBCK:FB04:LG01:DL2VERNIER', kind='normal',
                     doc='DL2 Energy [MeV]')
    vernier_percent_of_bend_energy = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML01:AO151',
                                         kind='normal',
                                         doc='Vernier Scan Range [%]')
    vernier_limit = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML01:CALC034', kind='normal',
                        doc='Vernier Limit [MeV]')
    vernier_ctrl_with_limits = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML01:CALC033',
                                   kind='normal',
                                   doc='Vernier Ctrl w/ limits [MeV]')
    hard_e_energy = Cpt(EpicsSignalRO, 'BEND:DMPH:400:BDES', kind='normal',
                        doc='Desired B-Field, Hard e-Energy [GeV/c]')
    soft_e_energy = Cpt(EpicsSignalRO, 'BEND:DMPS:400:BDES', kind='normal',
                        doc='Desired B-Field, Soft e-Energy [GeV/c]')

    def bykik_status(self):
        """
        Get status of bykik abort.

        Returns
        -------
            Bykik Abort Status
        """
        return self.bykik_abort.get()

    def bykik_disable(self):
        """Disable bykik abort."""
        return self.bykik_abort.put(value='Disable')

    def bykik_enable(self):
        """Enable bykik abort."""
        return self.bykik_abort.put(value='Enable')

    def bykik_get_period(self):
        """Get the number of events between bykik aborts."""
        return self.bykik_period.get()

    def bykik_set_period(self, period):
        """
        Set the number of events between bykik aborts.

        Parameters
        ----------
        period : number
        """
        return self.bykik_period.put(period)

    def __init__(self, prefix='', name='lcls', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)
