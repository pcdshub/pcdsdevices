#from lightpath import LightpathState
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt

from .analog_signals import FDQ
from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import (IMS, BeckhoffAxis, BeckhoffAxisNoOffset,
                          EpicsMotorInterface)

import enum
import logging
import time
import typing
from collections import namedtuple

import numpy as np
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from ophyd.status import MoveStatus

from .beam_stats import BeamEnergyRequest
from .epics_motor import IMS, EpicsMotorInterface
from .interface import BaseInterface, FltMvInterface#, LightpathMixin
from .pseudopos import (PseudoPositioner, PseudoSingleInterface, SyncAxis,
                        SyncAxisOffsetMode)
from .pv_positioner import PVPositionerIsClose
from .signal import InternalSignal
from .utils import doc_format_decorator, get_status_float

logger = logging.getLogger(__name__)

# Constants
si_111_dspacing = 3.1356011499587773

# Defaults
default_dspacing = si_111_dspacing


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


    tab_component_names = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def forward(self, pseudo_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the setpoint.

        Converts the requested energy to theta 1 and theta 2 (Bragg angle).
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        energy = pseudo_pos.energy
        theta = self.energyToSi111BraggAngle(energy)
        return self.RealPosition(theta=theta)

    def inverse(self, real_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the readback.

        Converts the real position of the DCCM theta motor to the calculated energy.
        """
        real_pos = self.RealPosition(*real_pos)
        theta = real_pos.theta
        energy = self.thetaToSi111energy(theta)
        return self.PseudoPosition(energy=energy)

    def energyToSi111BraggAngle(self, energy: float) -> float:
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
        dspacing = 3.13560114
        bragg_angle = np.rad2deg(np.arcsin(12398.419/energy/(2*dspacing)))
        return bragg_angle

    def thetaToSi111energy(self, theta):
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
        dspacing = 3.13560114
        energy = 12398.419/(2*dspacing*np.sin(np.deg2rad(theta)))
        return energy




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

    th1 = Cpt(BeckhoffAxis, ":MMS:TH1", doc="Bragg Upstream/TH1 Axis", kind="normal")
    th2 = Cpt(BeckhoffAxis, ":MMS:TH2", doc="Bragg Downstream/TH2 Axis", kind="normal")
    tx = Cpt(BeckhoffAxis, ":MMS:TX", doc="Translation X Axis", kind="normal")
    txd = Cpt(BeckhoffAxis, ":MMS:TXD", doc="YAG Diagnostic X Axis", kind="normal")
    tyd = Cpt(BeckhoffAxis, ":MMS:TYD", doc="YAG Diagnostic Y Axis", kind="normal")


    energy = Cpt(
        DCCMEnergy, '', kind='hinted',
        doc=(
            'PseudoPositioner that moves the theta motors in '
            'terms of the calculated DCCM energy.'
        ),
    )


