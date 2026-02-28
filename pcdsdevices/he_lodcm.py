import logging
from enum import Enum, auto

from ophyd.device import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis, BeckhoffAxisEPS
from .interface import BaseInterface, FltMvInterface
from .lakeshore import Lakeshore336
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)

logger = logging.getLogger(__name__)


class HE_LODCMEnergy(FltMvInterface, PseudoPositioner):
    energy = Cpt(
        PseudoSingleInterface,
        egu='keV',
        kind='hinted',
        limits=(),
        verbose_name='',
        doc=(
            'PseudoSingle that moves the calculated LODCM '
            'selected energy in keV.'
        ),
    )
    t1ry = Cpt(BeckhoffAxis, ':MMS:T1Ry', kind='normal', doc='Tower 1 rotation Y')
    t2ry = Cpt(BeckhoffAxis, ':MMS:T2Ry', kind='normal', doc='Tower 2 rotation Y')
    t2tz = Cpt(BeckhoffAxis, ':MMS:T2Tz', kind='normal', doc='Tower 2 translation Z')

    t1ty = Cpt(BeckhoffAxis, ':MMS:T1Ty', kind='normal', doc='Tower 1 translation Y')

    class Crystal(Enum):
        Si111 = auto()
        Si220 = auto()

    def get_crystal(self):
        rbv = self.t1ty.user_readback.get()
        if 0 < rbv < 1:
            return self.Crystal.Si111
        elif 1 < rbv < 2:
            return self.Crystal.Si220
        else:
            return None

    @classmethod
    def _get_real_positioners(cls):
        # Want to use t1ty to determine the crystal but not be part of the pseudoposition
        return [(attr, cpt) for attr, cpt in super()._get_real_positioners() if attr != 't1ty']

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Calculate a RealPosition from a given PseudoPosition.

        If the pseudo positioner is here at `pseudo_pos`, then this is where
        my real motor should be.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            The pseudo position input, a namedtuple.

        Returns
        -------
        real_pos : RealPosition
            The real position output, a namedtuple.
        """
        energy = self.PseudoPosition(*pseudo_pos).energy
        raise NotImplementedError
        return self.RealPosition(t1ry=0*energy,
                                 t2ry=0,
                                 t2tz=0)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Calculate a PseudoPosition from a given RealPosition.

        If the real motor is at this `real_pos`, then this is where my pseudo
        position should be.

        Parameters
        ----------
        real_pos : RealPosition
            The real position input.

        Returns
        -------
        pseudo_pos : PseudoPosition
            The pseudo position output.
        """
        real_pos = self.RealPosition(*real_pos)
        energy = 0
        raise NotImplementedError
        return self.PseudoPosition(energy=energy)


class HE_LODCM(BaseInterface, GroupDevice):
    energy = Cpt(HE_LODCMEnergy, '', kind='hinted', doc='')

    t1ty = Cpt(BeckhoffAxis, ':MMS:T1Ty', kind='normal', doc='Tower 1 translation Y')
    t1tx = Cpt(BeckhoffAxisEPS, ':MMS:T1Tx', kind='normal', doc='Tower 1 translation X')
    t1ry = Cpt(BeckhoffAxisEPS, ':MMS:T1Ry', kind='normal', doc='Tower 1 rotation Y')
    t1tp = Cpt(BeckhoffAxisEPS, ':MMS:T1Tp', kind='normal', doc='Tower 1 TP')
    t1rp = Cpt(BeckhoffAxisEPS, ':MMS:T1Rp', kind='normal', doc='Tower 1 RP')

    t2ty1 = Cpt(BeckhoffAxis, ':MMS:T2Ty', kind='normal', doc='Tower 2 translation Y 1')
    t2ty2 = Cpt(BeckhoffAxis, ':MMS:T2Ty2', kind='normal', doc='Tower 2 translation Y 2')
    t2tz = Cpt(BeckhoffAxisEPS, ':MMS:T2Tz', kind='normal', doc='Tower 2 translation Z')
    t2ry = Cpt(BeckhoffAxisEPS, ':MMS:T2Ry', kind='normal', doc='Tower 2 rotation Y')
    t2tn = Cpt(BeckhoffAxisEPS, ':MMS:T2Tn', kind='normal', doc='Tower 2 translation TN')
    t2tp = Cpt(BeckhoffAxisEPS, ':MMS:T2Tp', kind='normal', doc='Tower 2 translation TP')
    t2rp = Cpt(BeckhoffAxisEPS, ':MMS:T2Rp', kind='normal', doc='Tower 2 translation RP')

    d1ry = Cpt(BeckhoffAxisEPS, ':MMS:D1Ry', kind='normal', doc='Diagnostic 1 rotation Y')
    d1ty = Cpt(BeckhoffAxisEPS, ':MMS:D1Ty', kind='normal', doc='Diagnostic 1 translation Y')

    d2tx = Cpt(BeckhoffAxisEPS, ':MMS:D1Tx', kind='normal', doc='Diagnostic 2 translation X')
    d2ty = Cpt(BeckhoffAxisEPS, ':MMS:D1Ty', kind='normal', doc='Diagnostic 2 translation Y')

    tct1 = Cpt(Lakeshore336, ':TCT:01', kind='normal', doc='Crystal 1 temperature controller')
    tct2 = Cpt(Lakeshore336, ':TCT:02', kind='normal', doc='Crystal 2 temperature controller')
