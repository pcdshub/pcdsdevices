import logging

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO, Signal

from .beam_stats import BeamEnergyRequest
from .epics_motor import IMS, EpicsMotorInterface
from .inout import InOutPositioner
from .interface import FltMvInterface
from .pseudopos import (PseudoPositioner, PseudoSingleInterface, SyncAxis,
                        SyncAxisOffsetMode)
from .pv_positioner import PVPositionerIsClose

logger = logging.getLogger(__name__)

# Constants
si_111_dspacing = 3.1356011499587773
si_511_dspacing = 1.0452003833195924

# Defaults
default_theta0 = 14.9792 * np.pi/180
default_dspacing = si_111_dspacing
default_gr = 3.175
default_gd = 231.303


class CCMMotor(PVPositionerIsClose):
    """
    Goofy records used in the CCM.
    """

    # Tolerance from old xcs python code
    atol = 3e-4

    setpoint = Cpt(EpicsSignal, ":POSITIONSET", auto_monitor=True)
    readback = Cpt(EpicsSignalRO, ":POSITIONGET", auto_monitor=True,
                   kind='hinted')


class CCMPico(EpicsMotorInterface):
    """
    The Pico motors used here seem non-standard, as they are missing spg.

    They still need the direction_of_travel fix from PCDSMotorBase.
    This is a bit hacky for now, something should be done in the epics_motor
    file to accomodate these.
    """
    direction_of_travel = Cpt(Signal, kind='omitted')

    def _pos_changed(self, timestamp=None, old_value=None,
                     value=None, **kwargs):
        # Store the internal travelling direction of the motor to account for
        # the fact that our EPICS motor does not have TDIR field
        try:
            comparison = int(value > old_value)
            self.direction_of_travel.put(comparison)
        except TypeError:
            # We have some sort of null/None/default value
            logger.debug('Could not compare value=%s > old_value=%s',
                         value, old_value)
        # Pass information to PositionerBase
        super()._pos_changed(timestamp=timestamp, old_value=old_value,
                             value=value, **kwargs)


class CCMCalc(FltMvInterface, PseudoPositioner):
    """
    CCM calculation motors to move in terms of physics quantities.

    All new parameters are scientific constants, and the current docstring
    writer is not familiar with all of them, so I will omit the full
    description instead of giving a partial and possibly incorrect summary.
    """

    energy = Cpt(PseudoSingleInterface, egu='keV', kind='hinted',
                 limits=(4, 25), verbose_name='CCM Photon Energy')
    wavelength = Cpt(PseudoSingleInterface, egu='A', kind='normal')
    theta = Cpt(PseudoSingleInterface, egu='deg', kind='normal')
    energy_with_vernier = Cpt(PseudoSingleInterface, egu='keV',
                              kind='omitted')

    alio = Cpt(CCMMotor, '', kind='normal')
    energy_request = FCpt(BeamEnergyRequest, '{hutch}', kind='normal')

    tab_component_names = True

    def __init__(self, prefix, *args, theta0=default_theta0,
                 dspacing=default_dspacing, gr=default_gr, gd=default_gd,
                 hutch=None, **kwargs):
        self.theta0 = theta0
        self.dspacing = dspacing
        self.gr = gr
        self.gd = gd
        if hutch is not None:
            self.hutch = hutch
        # Put some effort into filling this automatically
        # CCM exists only in two hutches
        elif 'XPP' in prefix:
            self.hutch = 'XPP'
        elif 'XCS' in prefix:
            self.hutch = 'XCS'
        else:
            self.hutch = 'TST'
        super().__init__(prefix, *args, auto_target=False, **kwargs)

    def forward(self, pseudo_pos):
        """
        Take energy, wavelength, theta, or energy_with_vernier and map to
        alio and energy_request.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        # Figure out which one changed.
        energy_with_vernier, energy, wavelength, theta = None, None, None, None
        if not np.isclose(pseudo_pos.energy_with_vernier,
                          self.energy_with_vernier.position):
            energy_with_vernier = pseudo_pos.energy_with_vernier
        elif not np.isclose(pseudo_pos.energy, self.energy.position):
            energy = pseudo_pos.energy
        elif not np.isclose(pseudo_pos.wavelength, self.wavelength.position):
            wavelength = pseudo_pos.wavelength
        elif not np.isclose(pseudo_pos.theta, self.theta.position):
            theta = pseudo_pos.theta
        else:
            alio = self.alio.position
        logger.debug('Forward (move) calculation args: '
                     f'energy={energy}, wavelength={wavelength}, '
                     f'theta={theta}, '
                     f'energy_with_vernier={energy_with_vernier}')
        if energy_with_vernier is not None:
            energy = energy_with_vernier
            energy_request = energy_with_vernier * 1000
        else:
            energy_request = self.energy_request.setpoint.get()
        if energy is not None:
            wavelength = energy_to_wavelength(energy)
        if wavelength is not None:
            theta = wavelength_to_theta(wavelength, self.dspacing) * 180/np.pi
        if theta is not None:
            alio = theta_to_alio(theta * np.pi/180, self.theta0,
                                 self.gr, self.gd)
        logger.debug('Forward (move) calculation results: '
                     f'alio={alio}, energy_request={energy_request}')
        return self.RealPosition(alio=alio, energy_request=energy_request)

    def inverse(self, real_pos):
        """Take alio and map to energy, wavelength, and theta."""
        real_pos = self.RealPosition(*real_pos)
        theta = alio_to_theta(real_pos.alio, self.theta0, self.gr, self.gd)
        wavelength = theta_to_wavelength(theta, self.dspacing)
        energy = wavelength_to_energy(wavelength)
        return self.PseudoPosition(energy=energy,
                                   wavelength=wavelength,
                                   theta=theta*180/np.pi,
                                   energy_with_vernier=energy)


class CCMX(SyncAxis):
    """Combined motion of the CCM X motors."""
    down = FCpt(IMS, '{self.down_prefix}')
    up = FCpt(IMS, '{self.up_prefix}')

    offset_mode = SyncAxisOffsetMode.AUTO_FIXED
    tab_component_names = True

    def __init__(self, down_prefix, up_prefix, *args, **kwargs):
        self.down_prefix = down_prefix
        self.up_prefix = up_prefix
        super().__init__(down_prefix, *args, **kwargs)


class CCMY(SyncAxis):
    """Combined motion of the CCM Y motors."""
    down = FCpt(IMS, '{self.down_prefix}')
    up_north = FCpt(IMS, '{self.up_north_prefix}')
    up_south = FCpt(IMS, '{self.up_south_prefix}')

    offset_mode = SyncAxisOffsetMode.AUTO_FIXED
    tab_component_names = True

    def __init__(self, down_prefix, up_north_prefix, up_south_prefix,
                 *args, **kwargs):
        self.down_prefix = down_prefix
        self.up_north_prefix = up_north_prefix
        self.up_south_prefix = up_south_prefix
        super().__init__(down_prefix, *args, **kwargs)


class CCM(InOutPositioner):
    """
    The full CCM assembly.

    This requires a huge number of motor pv prefixes to be passed in, and they
    are all labelled accordingly.
    """

    calc = FCpt(CCMCalc, '{self.alio_prefix}', kind='hinted')
    theta2fine = FCpt(CCMMotor, '{self.theta2fine_prefix}', atol=0.01)
    theta2coarse = FCpt(CCMPico, '{self.theta2coarse_prefix}')
    chi2 = FCpt(CCMPico, '{self.chi2_prefix}')
    x = FCpt(CCMX,
             down_prefix='{self.x_down_prefix}',
             up_prefix='{self.x_up_prefix}',
             add_prefix=('down_prefix', 'up_prefix'),
             kind='omitted')
    y = FCpt(CCMY,
             down_prefix='{self.y_down_prefix}',
             up_north_prefix='{self.y_up_north_prefix}',
             up_south_prefix='{self.y_up_south_prefix}',
             add_prefix=('down_prefix', 'up_north_prefix', 'up_south_prefix'),
             kind='omitted')
    state = Cpt(AttributeSignal, attr='_state', kind='omitted')

    # Placeholder value. This represents "not full transmission".
    _transmission = {'IN': 0.9}

    tab_component_names = True

    def __init__(self, alio_prefix, theta2fine_prefix, theta2coarse_prefix,
                 chi2_prefix, x_down_prefix, x_up_prefix,
                 y_down_prefix, y_up_north_prefix, y_up_south_prefix,
                 in_pos, out_pos, *args,
                 theta0=default_theta0, dspacing=default_dspacing,
                 gr=default_gr, gd=default_gd, **kwargs):
        self.alio_prefix = alio_prefix
        self.theta2fine_prefix = theta2fine_prefix
        self.theta2coarse_prefix = theta2coarse_prefix
        self.chi2_prefix = chi2_prefix
        self.x_down_prefix = x_down_prefix
        self.x_up_prefix = x_up_prefix
        self.y_down_prefix = y_down_prefix
        self.y_up_north_prefix = y_up_north_prefix
        self.y_up_south_prefix = y_up_south_prefix
        self._in_pos = in_pos
        self._out_pos = out_pos
        super().__init__(alio_prefix, *args, **kwargs)
        self.calc.theta0 = theta0
        self.calc.dspacing = dspacing
        self.calc.gr = gr
        self.calc.gd = gd

    @property
    def _state(self):
        if np.isclose(self.x.position, self._in_pos):
            return 1
        elif np.isclose(self.x.position, self._out_pos):
            return 2
        else:
            return 0

    @_state.setter
    def _state(self, value):
        if value == 1:
            self.x.move(self._in_pos, wait=False)
        elif value == 2:
            self.x.move(self._out_pos, wait=False)


# Calculations between alio position and energy, with all intermediates.
def theta_to_alio(theta, theta0, gr, gd):
    """
    Converts theta angle (rad) to alio position (mm).

    Theta_B:       scattering angle, the angle reduces when rotating clockwise
                   (Bragg angle)
    Theta_0:       scattering angle offset of the Si (111) first crystal
    Delta_Theta:   the effective scattering angle (adjusted with Alio stage)
    R = 0.003175m: radius of the sapphire ball connected to the Alio stage
    D = 0.232156m: distance between the Theta_B rotation axis and the center
                   of the saphire sphere located on the Alio stage.
                   note: The current value that we're using for D is 0.231303 -
                   possibly measured by metrology

    Theta_B = Theta_0 + Delta_Theta
    Conversion formula:
    x = f(Delta_Theta) = D * tan(Delta_Theta)+(R/cos(Delta_Theda))-R
    Note that for ∆θ = 0, x = R
    """
    t_rad = theta - theta0
    return gr * (1 / np.cos(t_rad) - 1) + gd * np.tan(t_rad)


def alio_to_theta(alio, theta0, gr, gd):
    """
    Converts alio position (mm) to theta angle (rad).

    Conversion function
    theta_angle = f(x) = 2arctan * [(sqrt(x^2 + D^2 + 2Rx) - D)/(2R + x)]
    Note that for x = −R, θ = 2 arctan(−R/D)
    """
    return theta0 + 2 * np.arctan(
         (np.sqrt(alio ** 2 + gd ** 2 + 2 * gr * alio) - gd) / (2 * gr + alio)
     )


def wavelength_to_theta(wavelength, dspacing):
    """Converts wavelength (A) to theta angle (rad)."""
    return np.arcsin(wavelength/2/dspacing)


def theta_to_wavelength(theta, dspacing):
    """Converts theta angle (rad) to wavelength (A)."""
    return 2*dspacing*np.sin(theta)


def energy_to_wavelength(energy):
    """Converts photon energy (keV) to wavelength (A)."""
    return 12.39842/energy


def wavelength_to_energy(wavelength):
    """Converts wavelength (A) to photon energy (keV)."""
    return 12.39842/wavelength
