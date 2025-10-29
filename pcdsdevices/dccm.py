import logging
import time
import typing
from collections import namedtuple
from enum import Enum
from typing import Optional

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import AttributeSignal, InternalSignal

from .beam_stats import BeamEnergyRequest
from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface, FltMvInterface
from .pmps import TwinCATStatePMPS
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)
from .variety import set_metadata

logger = logging.getLogger(__name__)


class CrystalIndex(float, Enum):
    Si111 = 3.1356011499587773
    Si333 = 1.0452003825497919


class DCCMEnergy(FltMvInterface, PseudoPositioner):
    """
    DCCM energy motor.

    Calculates the current DCCM energy using the DCCM angle, and
    requests moves to the DCCM motors based on energy requests.

    Presents itself like a motor.

    Parameters
    ----------
    prefix : str
        The PV prefix of the DCCM motor, e.g. XPP:MON:MPZ:07A
    """

    _extra_sig_md = {
        'precision': 3,
        'units': 'mrad',
    }
    high_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind='omitted',
    )
    low_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind='omitted',
    )

    def __init__(self, prefix: str, *, name: str, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.low_limit_travel.put(self.energy.low_limit, internal=True)
        self.high_limit_travel.put(self.energy.high_limit, internal=True)
        self.energy.subscribe(self.update_readback, event_type=self.energy.SUB_READBACK)

    def update_readback(self, *args, **kwargs):
        rb = self.energy.readback
        rb._run_subs(sub_type=rb.SUB_VALUE, old_value=rb._readback, value=rb.get(), timestamp=time.time())

    # Pseudo motor and real motor
    energy = Cpt(
        PseudoSingleInterface,
        egu='keV',
        kind='hinted',
        limits=(4, 25),
        verbose_name='DCCM Photon Energy',
        doc=(
            'PseudoSingle that moves the calculated DCCM '
            'selected energy in keV.'
        ),
    )

    th1 = Cpt(BeckhoffAxis, ":MMS:TH1", doc="Bragg Upstream/TH1 Axis", kind="normal", name='th1')
    th2 = Cpt(BeckhoffAxis, ":MMS:TH2", doc="Bragg Upstream/TH2 Axis", kind="normal", name='th2')
    # th1 = Cpt(BeckhoffAxis, ":mtr1", doc="Bragg Upstream/TH1 Axis", kind="normal", name='th1')
    # th2 = Cpt(BeckhoffAxis, ":mtr2", doc="Bragg Upstream/TH2 Axis", kind="normal", name='th2')

    _crystal_index = CrystalIndex.Si111
    crystal_index = Cpt(AttributeSignal, attr='_crystal_index', kind='omitted', write_access=False)

    @property
    def _crystal_index_name(self):
        return self._crystal_index.name
    crystal_index_name = Cpt(AttributeSignal, attr='_crystal_index_name', kind='omitted', write_access=False)

    def update_crystal_index(self, crystal_index):
        if not isinstance(crystal_index, CrystalIndex):
            return
        self.crystal_index._metadata.update(write_access=True)
        self.crystal_index.put(crystal_index)
        self.crystal_index._metadata.update(write_access=False)
        old_value = self.energy.readback.get()
        self._my_move = True
        self._update_position()
        self.energy.readback._run_subs(sub_type=self.energy.readback.SUB_VALUE, old_value=old_value, value=self.energy.readback.get(), timestamp=time.time())
        cin = self.crystal_index_name
        cin._run_subs(sub_type=cin.SUB_VALUE, old_value=cin._readback, value=cin.get(), timestamp=time.time())

    switch_crystal_index = Cpt(AttributeSignal, attr='_switch_crystal_index')
    set_metadata(switch_crystal_index, dict(variety='command', value=0))

    @property
    def _switch_crystal_index(self):
        return 0

    @_switch_crystal_index.setter
    def _switch_crystal_index(self, value):
        if self._crystal_index is CrystalIndex.Si111:
            self.update_crystal_index(CrystalIndex.Si333)
        elif self._crystal_index is CrystalIndex.Si333:
            self.update_crystal_index(CrystalIndex.Si111)

    @property
    def dspacing(self):
        return self._crystal_index.value

    tab_component_names = True

    @pseudo_position_argument
    def forward(self, pseudo_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the setpoint.
        Converts the requested energy to theta 1 and theta 2 (Bragg angle).
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        energy = pseudo_pos.energy
        theta = self.energyToBraggAngle(energy)
        return self.RealPosition(th1=theta, th2=theta)

    @real_position_argument
    def inverse(self, real_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the readback.

        Converts the real position of the DCCM theta motor to the calculated energy.
        """
        real_pos = self.RealPosition(*real_pos)
        theta = real_pos.th1
        if theta < 0.1:
            energy = float('NaN')
        else:
            energy = self.thetaToEnergy(theta)
        return self.PseudoPosition(energy=energy)

    def energyToBraggAngle(self, energy: float) -> float:
        """
        Converts energy to Bragg angle theta

        Parameters
        ----------
        energy : float
            The photon energy (color) in keV.

        Returns
        ---------
        Bragg angle: float
            The angle in degrees
        """
        energy = energy * 1000
        bragg_angle = np.rad2deg(np.arcsin(np.float64(12398.419)/energy/(2*self.dspacing)))
        return bragg_angle

    def thetaToEnergy(self, theta):
        """
        Converts dccm theta angle to energy.

        Parameters
        ----------
        energy : float
            The Bragg angle theta in degrees

        Returns:
        ----------
        energy: float
             The photon energy (color) in keV.
        """
        energy = 12398.419/(2*self.dspacing*np.sin(np.deg2rad(np.float64(theta))))
        return energy/1000


class DCCMEnergyWithVernier(DCCMEnergy):
    """
    DCCM energy motor and the vernier.

    Moves the DCCM theta based on the requested energy using the values
    of the calculation constants, and reports the current energy
    based on the motor's position.

    Also moves the vernier when a move is requested to the DCCM motor.
    Note that the vernier is in units of eV, while the energy
    calculations are in units of keV.

    Parameters
    ----------
    prefix : str
        The PV prefix of the theta motor, e.g. XPP:MON:MPZ:07A
    hutch : str, optional
        The hutch we're in. This informs us as to which vernier
        PVs to write to. If omitted, we can guess this from the
        prefix.
    """
    acr_energy = FCpt(BeamEnergyRequest, '{hutch}', kind='normal',
                      doc='Requests ACR to move the Vernier.')

    # These are duplicate warnings with main energy motor
    _enable_warn_constants: bool = False
    hutch: str

    def __init__(
        self,
        prefix: str,
        hutch: Optional[str] = None,
        **kwargs
    ):
        # Determine which hutch to use
        if hutch is not None:
            self.hutch = hutch
        elif 'CXI' in prefix:
            self.hutch = 'CXI'
        elif 'MEC' in prefix:
            self.hutch = 'MEC'
        elif 'MFX' in prefix:
            self.hutch = 'MFX'
        elif 'XCS' in prefix:
            self.hutch = 'XCS'
        else:
            self.hutch = 'TST'
        super().__init__(prefix, **kwargs)

    @pseudo_position_argument
    def forward(self, pseudo_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the setpoint.
        Converts the requested energy to theta 1 and theta 2 (Bragg angle).
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        energy = pseudo_pos.energy
        theta = self.energyToBraggAngle(energy)
        vernier = energy * 1000
        return self.RealPosition(th1=theta, th2=theta, acr_energy=vernier)


class DCCMEnergyWithACRStatus(DCCMEnergyWithVernier):
    """
    CCM energy motor and ACR beam energy request with status.
    Note that in this case vernier indicates any ways that ACR will act on the
    photon energy request. This includes the Vernier, but can also lead to
    motion of the undulators or the K.

    Parameters
    ----------
    prefix : str
        The PV prefix of the Alio motor, e.g. XPP:MON:MPZ:07A
    hutch : str, optional
        The hutch we're in. This informs us as to which vernier
        PVs to write to. If omitted, we can guess this from the
        prefix.
    acr_status_sufix : str
        Prefix to the SIOC PV that ACR uses to report the move status.
        For HXR this usually is 'AO805'.
    """
    acr_energy = FCpt(BeamEnergyRequest, '{hutch}',
                      pv_index='{pv_index}',
                      acr_status_suffix='{acr_status_suffix}',
                      add_prefix=('suffix', 'write_pv', 'pv_index',
                                  'acr_status_suffix'),
                      kind='normal',
                      doc='Requests ACR to move the energy.')

    def __init__(
        self,
        prefix: str,
        hutch: typing.Optional[str] = None,
        acr_status_suffix='AO805',
        pv_index=2,
        **kwargs
    ):
        self.acr_status_suffix = acr_status_suffix
        self.pv_index = pv_index
        super().__init__(prefix, hutch=hutch, **kwargs)


class DCCMTarget(TwinCATStatePMPS):
    config = UpCpt(state_count=2)
    _in_if_not_out = True


class DCCM(BaseInterface, GroupDevice):
    """
    The full DCCM assembly.

    Double Channel Cut Monochrometer controlled with a Beckhoff PLC.
    This includes five axes in total:
        - 2 for crystal manipulation (TH1/Upstream and TH2/Downstream)
        - 1 for chamber translation in x direction (TX)
    - 2 for YAG diagnostics (TXD and TYD)

    Parameters
    ----------
    prefix : str
        Base PV for DCCM motors
    name : str, keyword-only
        name to use in bluesky
    """

    tab_component_names = True

    tx_state = Cpt(DCCMTarget, ':MMS:STATE', kind='hinted', doc='Control of TX axis via saved positions.')

    energy = Cpt(
        DCCMEnergy, '', kind='hinted',
        doc=(
            'PseudoPositioner that moves the theta motors in '
            'terms of the calculated DCCM energy.'
        ),
    )

    energy_with_vernier = FCpt(
        DCCMEnergyWithVernier, '{self.prefix}', kind='normal',
        hutch='{hutch}',
        add_prefix=('suffix', 'write_pv', 'hutch'),
        doc=(
            'PseudoPositioner that moves the theta motor in '
            'terms of the calculated DCCM energy while '
            'also requesting a vernier move.'
        ),
    )
    energy_with_acr_status = FCpt(
        DCCMEnergyWithACRStatus, '{self.prefix}', kind='normal',
        hutch='{hutch}',
        pv_index='{acr_status_pv_index}',
        acr_status_suffix='{acr_status_suffix}',
        add_prefix=('suffix', 'write_pv', 'acr_status_suffix', 'pv_index', 'hutch'),
        doc=(
            'PseudoPositioner that moves the alio in '
            'terms of the calculated CCM energy while '
            'also requesting an energy change to ACR. '
            'This will wait on ACR to complete the move.'
        ),
    )

    th1 = Cpt(BeckhoffAxis, ":MMS:TH1", doc="Bragg Upstream/TH1 Axis", kind="normal")
    th2 = Cpt(BeckhoffAxis, ":MMS:TH2", doc="Bragg Downstream/TH2 Axis", kind="normal")
    tx = Cpt(BeckhoffAxis, ":MMS:TX", doc="Translation X Axis", kind="normal")
    txd = Cpt(BeckhoffAxis, ":MMS:TXD", doc="YAG Diagnostic X Axis", kind="normal")
    tyd = Cpt(BeckhoffAxis, ":MMS:TYD", doc="YAG Diagnostic Y Axis", kind="normal")

    def __init__(
            self,
            prefix: str = "SP1L0:DCCM",
            hutch: str = '',
            acr_status_suffix: str = 'AO805',
            acr_status_pv_index: int = 2,
            **kwargs
    ):
        self.hutch = hutch
        self.acr_status_suffix = acr_status_suffix
        self.acr_status_pv_index = acr_status_pv_index
        super().__init__(prefix, **kwargs)
