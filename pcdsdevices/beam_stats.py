import logging
from typing import Optional

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.positioner import PositionerBase
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO
from ophyd.sim import fake_device_cache, make_fake_device

from .interface import BaseInterface, FltMvInterface
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


class BeamEnergyRequest(FltMvInterface, Device, PositionerBase):
    """
    Positioner to request beam color changes from ACR in eV.

    It is up to ACR how to and whether to fulfill these requests. This is often
    fulfilled by moving the Vernier but can also be a more involved process.

    There are two variants to this device that are implemented in classes
    below.

    If we get a reference to an ACR PV to use for waiting, then that can be
    passed in as the acr_status_suffix kwarg. This PV will be used to determine
    when motion has completed. This behavior is implemented in the
    `BeamEnergyRequestACRWait` class.

    If we don't get a reference to an ACR PV to use for waiting, then
    motion is immedately considered "done", but will not execute unless the
    requested position delta is larger than the tolerance. The default
    tolerance here is 30 eV, but this can be changed on a per-instance basis
    by passing ``atol`` into the initializer, or on a per-subclass basis by
    overriding the default. This is implemented in the
    `BeamEnergyRequestNoWait` class.

    Parameters
    ----------
    prefix : str
        PV prefix for the request setpoint. This should always be a hutch name.

    name : str, required keyword
        Name to use for this device in log messages, data streams, etc.

    skip_small_moves : bool, optional
        Has no effect if using the wait-on-PV version of the class, but will
        take effect for the no-wait version of the class.
        Defaults to True, which ignores move requests that are smaller than the
        atol factor. If False, we'll perform every requested move.
        This can be very useful for synchronized energy scans where the ACR
        side of the process can be very slow, but does not necessarily need to
        happen at every step. Rather than design complicated scan patterns, we
        can skip the small moves here and move the monochromater and beam
        request devices in parallel.

    atol : int, optional
        Has no effect if using the wait-on-PV version of the class, but will
        take effect for the no-wait version of the class.
        Absolute tolerance that determines when the move is done and when to
        skip moves using the skip_small_moves parameter.

    line : str, optional
        Whether to use the K line or L line PV. If provided this should be a
        string with a single character. The K line PVs have "EPHOTK"
        in them, the L line PVs just have "EPHOT". This will default to the
        line associated with the prefix hutch name, or to L line failing that.

    bunch : int, optional
        Whether to move the first bunch (1) or the second bunch (2). This is
        only relevant for 2-color mode. Defaults to bunch 1.

    acr_status_suffix : str, optional
        If provided, we'll wait on the ACR PV specified by
        SIOC:SYS0:ML07:{suffix}. The selected PV should be 0 while the device
        is moving and 1 when it is done.
    """
    setpoint = FCpt(
        EpicsSignal,
        '{prefix}:USER:MCC:EPHOT{line_text}:SET{bunch}',
        kind='hinted',
        doc=(
            'The setpoint PV that acr listens on to update the '
            'vernier or undulator PVs as appropriate.'
        ),
    )
    ref = FCpt(
        EpicsSignal,
        '{prefix}:USER:MCC:EPHOT{line_text}:REF{bunch}',
        kind='normal',
        doc=(
            'A reference PV for the photon energy at the nominal '
            'position of the vernier or undulator.'
        ),
    )

    line_text_dict = {
        'K': 'K',
        'L': '',
    }
    for k_hutch in ('k', 'TMO', 'RIX'):
        line_text_dict[k_hutch] = line_text_dict['K']
    for l_hutch in ('l', 'XPP', 'XCS', 'MFX', 'CXI', 'MEC'):
        line_text_dict[l_hutch] = line_text_dict['L']

    def __new__(
        cls,
        *args,
        acr_status_suffix: Optional[str] = None,
        **kwargs
    ):
        if cls is not BeamEnergyRequest:
            return super().__new__(cls)
        if acr_status_suffix is None:
            return super().__new__(BeamEnergyRequestNoWait)
        return super().__new__(BeamEnergyRequestACRWait)

    def __init__(
        self,
        prefix: str,
        *,
        name: str,
        line: Optional[str] = None,
        bunch: int = 1,
        acr_status_suffix: Optional[str] = None,
        **kwargs
    ):
        self.line_text = self.line_text_dict.get(line or prefix, '')
        self.bunch = bunch
        self.acr_status_suffix = acr_status_suffix
        super().__init__(prefix, name=name, **kwargs)


class BeamEnergyRequestNoWait(BeamEnergyRequest, PVPositionerDone):
    """
    BeamEnergyRequest variant that does not wait on a PV.

    It will report done immediately and ignore moves that are smaller than
    atol.
    """
    atol = 5

    # All done-related functionality is inherited from PVPositionerDone
    # Just implement skip_small_moves's default
    def __init__(self, *args, skip_small_moves: bool = True, **kwargs):
        super().__init__(*args, skip_small_moves=skip_small_moves, **kwargs)


class BeamEnergyRequestACRWait(BeamEnergyRequest, PVPositioner):
    """
    BeamEnergyRequest variant that does wait on a PV.

    It will report done when the ACR status PV indicates done and will
    not use the atol parameter.
    """
    # All the logic is implemented in parent classes, just pick the PV
    done = FCpt(
        EpicsSignal,
        'SIOC:SYS0:ML07:{acr_status_suffix}',
        kind='normal',
        doc=(
            'PV that is 0 while the motors are moving and 1 when ACR is '
            'ready for a new request. ACR can pick which of these PVs '
            'to use to report status.'
        )
    )
    done_value = 1


_FakeBeamEnergyRequestNoWait = make_fake_device(BeamEnergyRequestNoWait)
_FakeBeamEnergyRequestACRWait = make_fake_device(BeamEnergyRequestACRWait)
_FakeBeamEnergyRequest = make_fake_device(BeamEnergyRequest)


class FakeBeamEnergyRequest(_FakeBeamEnergyRequest):
    """
    Required setup for fake classes to work properly with __new__ splitting
    """
    def __new__(
        cls,
        *args,
        acr_status_suffix: Optional[str] = None,
        **kwargs
    ):
        if cls is not FakeBeamEnergyRequest:
            return super().__new__(cls)
        if acr_status_suffix is None:
            return super().__new__(FakeBeamEnergyRequestNoWait)
        return super().__new__(FakeBeamEnergyRequestACRWait)


class FakeBeamEnergyRequestNoWait(
    _FakeBeamEnergyRequestNoWait,
    FakeBeamEnergyRequest,
):
    ...


class FakeBeamEnergyRequestACRWait(
    _FakeBeamEnergyRequestACRWait,
    FakeBeamEnergyRequest,
):
    ...


fake_device_cache[BeamEnergyRequestNoWait] = FakeBeamEnergyRequestNoWait
fake_device_cache[BeamEnergyRequestACRWait] = FakeBeamEnergyRequestACRWait
fake_device_cache[BeamEnergyRequest] = FakeBeamEnergyRequest


class LCLS(BaseInterface, Device):
    """
    Object to query machine Lcls Linac status.
    """

    tab_component_names = True

    tab_whitelist = ['bykik_status', 'bykik_disable', 'bykik_enable',
                     'bykik_get_period', 'bykik_set_period']

    bunch_charge = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO470', kind='normal',
                       doc='Bunch charge [nC]')
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
