from dataclasses import dataclass
from typing import Any

import numpy as np
from ophyd.device import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis, BeckhoffAxisEPS
from .interface import BaseInterface, FltMvInterface
from .lakeshore import Lakeshore336
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)
from .utils import get_status_float, get_status_value


@dataclass(frozen=True)
class Crystal:
    name: str
    d_spacing: float  # m
    t1ty_range: tuple[float, float]
    t2ty_range: tuple[float, float]


SI111 = Crystal("Si111", 3.1355e-7, t1ty_range=(0.1, 15), t2ty_range=(0.1, 15))
SI220 = Crystal("Si220", 1.9201e-7, t1ty_range=(-15, -0.1), t2ty_range=(-15, -0.1))

GRATING_DISTANCE = 28.6e3  # distance of the grating to the center of rotation of crystal 1 in meters.
IM2L0_DISTANCE = 7.3e3  # distance of iml2 from the center of rotation of crystal 1 in meters.
GAP = 599.0  # horizontal gap between the two crystals in mm.


class HE_LODCMEnergy(FltMvInterface, PseudoPositioner):
    energy = Cpt(
        PseudoSingleInterface,
        egu='keV',
        kind='hinted',
        limits=(4, 25),
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
    t2ty1 = Cpt(BeckhoffAxis, ':MMS:T2Ty', kind='normal', doc='Tower 2 translation Y 1')
    t2ty2 = Cpt(BeckhoffAxis, ':MMS:T2Ty2', kind='normal', doc='Tower 2 translation Y 2')

    tab_component_names = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grating_period = None  # grating perdiod in mm. Proper implementation to follow

    def get_crystal(self) -> Crystal:
        """
        Get the current crystal type from tower vertical positions.

        Returns
        -------
        Crystal
            SI111 or SI220 based on t1ty and t2ty readbacks.

        Raises
        ------
        RuntimeError
            If t1ty/t2ty positions are invalid or crystal types mismatch.
        """
        rbv_t1ty = self.t1ty.user_readback.get()
        rbv_t2ty1 = self.t2ty1.user_readback.get()
        rbv_t2ty2 = self.t2ty2.user_readback.get()

        for crystal in (SI111, SI220):
            if crystal.t1ty_range[0] <= rbv_t1ty <= crystal.t1ty_range[1]:
                t1_crystal = crystal
                break
        else:
            raise RuntimeError("Invalid t1ty position for determining crystal type")

        for crystal in (SI111, SI220):
            if (crystal.t2ty_range[0] <= rbv_t2ty1 <= crystal.t2ty_range[1]
                    and crystal.t2ty_range[0] <= rbv_t2ty2 <= crystal.t2ty_range[1]):
                t2_crystal = crystal
                break
        else:
            raise RuntimeError("Invalid t2ty1 and t2ty2 positions for determining crystal type")

        if t1_crystal != t2_crystal:
            raise RuntimeError("Crystal types do not match between towers")

        return t1_crystal

    def _energy_from_theta(self, theta_deg: float, crystal: Crystal) -> float:
        """
        Calculate energy from Bragg angle.

        Parameters
        ----------
        theta_deg : float
            Bragg angle in degrees.
        crystal : Crystal
            Crystal object with d-spacing.

        Returns
        -------
        float
            Energy in keV.
        """
        theta_rad = np.deg2rad(theta_deg)

        if self.grating_period is not None:
            grating_correction = np.sqrt(1 + (2 * crystal.d_spacing / self.grating_period) ** 2
                                         - 4 * crystal.d_spacing / self.grating_period * np.cos(theta_rad))
        else:
            grating_correction = 1

        wavelength_mm = 2 * crystal.d_spacing * np.sin(theta_rad) / grating_correction
        wavelength_nm = wavelength_mm * 1e6
        energy_keV = 1.2398 / wavelength_nm
        return energy_keV

    def _pos_from_energy(self, energy: float) -> tuple[float, float]:
        """
        Calculate motor positions from target energy.

        Parameters
        ----------
        energy : float
            Target energy in keV (4-25).

        Returns
        -------
        tuple[float, float]
            Tuple of (theta_degrees, t2tz_position).
        """
        crystal = self.get_crystal()

        wavelength_mm = (1.2398 / energy) * 1e-6
        bragg_rad = np.arcsin(wavelength_mm / crystal.d_spacing / 2)

        grating_angle_rad = 0

        if self.grating_period is not None:
            grating_angle_rad = np.arcsin(wavelength_mm / self.grating_period)
        else:
            grating_angle_rad = 0

        gap_t2tz = GAP * (np.cos(2 * bragg_rad - grating_angle_rad) * np.sin(bragg_rad)
                          / np.sin(2 * bragg_rad) / np.sin(bragg_rad - grating_angle_rad))

        grating_t2tz = (1 - np.sin(bragg_rad) * np.sin(2 * bragg_rad - grating_angle_rad)
                        / np.sin(2 * bragg_rad) / np.sin(bragg_rad - grating_angle_rad))
        grating_t2tz *= (GRATING_DISTANCE + IM2L0_DISTANCE)

        t2tz_pos = gap_t2tz + grating_t2tz
        theta_pos = np.rad2deg(bragg_rad - grating_angle_rad)

        return (theta_pos, t2tz_pos)

    @classmethod
    def _get_real_positioners(cls) -> list:
        """
        Override to exclude crystal detection motors.

        Returns
        -------
        list
            List of (attr, cpt) tuples excluding t1ty, t2ty1, t2ty2.
        """
        exclude = {'t1ty', 't2ty1', 't2ty2'}
        return [(attr, cpt) for attr, cpt in super()._get_real_positioners()
                if attr not in exclude]

    @pseudo_position_argument
    def forward(self, pseudo_pos: Any) -> Any:
        """
        Convert energy to motor positions.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            With .energy attribute.

        Returns
        -------
        RealPosition
            With t1ry, t2ry, t2tz attributes.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        th, t2tz = self._pos_from_energy(energy=pseudo_pos.energy)

        return self.RealPosition(t1ry=th,
                                 t2ry=th,
                                 t2tz=t2tz)

    @real_position_argument
    def inverse(self, real_pos: Any) -> Any:
        """
        Convert motor positions to energy.

        Parameters
        ----------
        real_pos : RealPosition
            With .t1ry attribute.

        Returns
        -------
        PseudoPosition
            With .energy attribute, or NaN if crystal detection fails.
        """
        try:
            crystal = self.get_crystal()
        except Exception:
            return self.PseudoPosition(energy=np.NaN)

        real_pos = self.RealPosition(*real_pos)
        theta_deg = real_pos.t1ry

        energy_keV = self._energy_from_theta(theta_deg, crystal)
        return self.PseudoPosition(energy=energy_keV)


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

    tab_component_names = True

    def __init__(self, prefix, *args, **kwargs):
        super().__init__(prefix=prefix, *args, **kwargs)

        # Aliases
        self.E = self.energy.energy

    def format_status_info(self, status_info):
        """
        Format status info for display.

        Parameters
        ----------
        status_info : dict
            Nested dictionary with motor/channel status data.

        Returns
        -------
        str
            Formatted multi-line status string.
        """
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
