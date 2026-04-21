import logging
from enum import Enum, auto

from ophyd.device import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis, BeckhoffAxisEPS
from .interface import BaseInterface, FltMvInterface
from .lakeshore import Lakeshore336
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)
from .utils import get_status_float, get_status_value

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

    d2tx = Cpt(BeckhoffAxisEPS, ':MMS:D2Tx', kind='normal', doc='Diagnostic 2 translation X')
    d2ty = Cpt(BeckhoffAxisEPS, ':MMS:D2Ty', kind='normal', doc='Diagnostic 2 translation Y')

    tct1 = Cpt(Lakeshore336, ':TCT:01', kind='normal', doc='Crystal 1 temperature controller')
    tct2 = Cpt(Lakeshore336, ':TCT:02', kind='normal', doc='Crystal 2 temperature controller')

    def format_status_info(self, status_info):
        energy = get_status_float(status_info, 'energy', 'value')

        def motor_status(attr, status_info):
            units = get_status_value(
                status_info, attr, 'user_setpoint', 'units')
            user = get_status_float(
                status_info, attr, 'position')
            dial = get_status_float(
                status_info, attr, 'dial_position', 'value')
            return units, user, dial

        t1ty_units, t1ty_user, t1ty_dial = motor_status('t1ty', status_info)
        t1tx_units, t1tx_user, t1tx_dial = motor_status('t1tx', status_info)
        t1ry_units, t1ry_user, t1ry_dial = motor_status('t1ry', status_info)
        t1tp_units, t1tp_user, t1tp_dial = motor_status('t1tp', status_info)
        t1rp_units, t1rp_user, t1rp_dial = motor_status('t1rp', status_info)

        t2ty1_units, t2ty1_user, t2ty1_dial = motor_status('t2ty1', status_info)
        t2ty2_units, t2ty2_user, t2ty2_dial = motor_status('t2ty2', status_info)
        t2tz_units, t2tz_user, t2tz_dial = motor_status('t2tz', status_info)
        t2ry_units, t2ry_user, t2ry_dial = motor_status('t2ry', status_info)
        t2tn_units, t2tn_user, t2tn_dial = motor_status('t2tn', status_info)
        t2tp_units, t2tp_user, t2tp_dial = motor_status('t2tp', status_info)
        t2rp_units, t2rp_user, t2rp_dial = motor_status('t2rp', status_info)
        d1ry_units, d1ry_user, d1ry_dial = motor_status('d1ry', status_info)
        d1ty_units, d1ty_user, d1ty_dial = motor_status('d1ty', status_info)
        d2tx_units, d2tx_user, d2tx_dial = motor_status('d2tx', status_info)
        d2ty_units, d2ty_user, d2ty_dial = motor_status('d2ty', status_info)

        def lakeshore_status(attr, channel, status_info):
            units = get_status_value(
                status_info, attr, f'temp_{channel}', 'units', 'value')
            temp = get_status_float(
                status_info, attr, f'temp_{channel}', 'temp', 'value')
            return units, temp
        tct1A_units, tct1A_temp = lakeshore_status('tct1', 'A', status_info)
        tct1B_units, tct1B_temp = lakeshore_status('tct1', 'B', status_info)
        tct1C_units, tct1C_temp = lakeshore_status('tct1', 'C', status_info)
        tct1D_units, tct1D_temp = lakeshore_status('tct1', 'D', status_info)
        tct2A_units, tct2A_temp = lakeshore_status('tct2', 'A', status_info)
        tct2B_units, tct2B_temp = lakeshore_status('tct2', 'B', status_info)
        tct2C_units, tct2C_temp = lakeshore_status('tct2', 'C', status_info)
        tct2D_units, tct2D_temp = lakeshore_status('tct2', 'D', status_info)

        def form(left_str, center_str, right_str):
            return f'{left_str:<16}{center_str:>26}{right_str:>26}'

        return f"""{self.prefix} Status
        Energy: {energy} [keV]
        -----------------------------------------------------------------
        {form(' ', 'Crystal Tower 1', 'Crystal Tower 2')}
        {form(f'y1 [{t1ty_units}]', f'{t1ty_user} ({t1ty_dial})', f'{t2ty1_user} ({t2ty1_dial})')}
        {form(f'y2 [{t2ty2_units}]', '', f'{t2ty2_user} ({t2ty2_dial})')}
        {form(f'x [{t1tx_units}]', f'{t1tx_user} ({t1tx_dial})', '')}
        {form(f'z [{t2tz_units}]', '', f'{t2tz_user} ({t2tz_dial})')}
        {form(f'ry [{t1ry_units}]', f'{t1ry_user} ({t1ry_dial})', f'{t2ry_user} ({t2ry_dial})')}
        {form(f'tn [{t2tn_units}]', f'', f'{t2tn_user} ({t2tn_dial})')}
        {form(f'tp [{t1tp_units}]', f'{t1tp_user} ({t1tp_dial})', f'{t2tp_user} ({t2tp_dial})')}
        {form(f'rp [{t1rp_units}]', f'{t1rp_user} ({t1rp_dial})', f'{t2rp_user} ({t2rp_dial})')}
        -----------------------------------------------------------------
        {form(' ', 'Diagnostic Tower', ' ')}
        {form(f'd1ry [{d1ry_units}]', f'{d1ry_user} ({d1ry_dial})', '')}
        {form(f'd1ty [{d1ty_units}]', f'{d1ty_user} ({d1ty_dial})', '')}
        {form(f'd2tx [{d2tx_units}]', f'{d2tx_user} ({d2tx_dial})', '')}
        {form(f'd2ty [{d2ty_units}]', f'{d2ty_user} ({d2ty_dial})', '')}
        -----------------------------------------------------------------
        {form(' ', 'Lakeshore 1', 'Lakeshore 2')}
        {form(f'A [{tct1A_units}]', f'{tct1A_temp}', f'{tct2A_temp}')}
        {form(f'B [{tct1B_units}]', f'{tct1B_temp}', f'{tct2B_temp}')}
        {form(f'C [{tct1C_units}]', f'{tct1C_temp}', f'{tct2C_temp}')}
        {form(f'D [{tct1D_units}]', f'{tct1D_temp}', f'{tct2D_temp}')}
        """
