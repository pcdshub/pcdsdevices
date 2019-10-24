import logging
import time

import numpy as np
from ophyd.device import Component as Cpt, FormattedComponent as FCpt
from ophyd.pseudopos import PseudoPositioner
from ophyd.pv_positioner import PVPositionerPC
from ophyd.signal import EpicsSignal, EpicsSignalRO, AttributeSignal

from .epics_motor import IMS
from .inout import InOutPositioner
from .interface import FltMvInterface
from .pseudopos import SyncAxesBase, PseudoSingleInterface

logger = logging.getLogger(__name__)

# Constants
si_111_dspacing = 3.1356011499587773
si_511_dspacing = 1.0452003833195924

# Defaults
default_theta0 = 14.9792 * np.pi/180
default_dspacing = si_111_dspacing
default_gr = 3.175
default_gd = 231.303


class CCMMotor(PVPositionerPC, FltMvInterface):
    """
    Goofy records used in the CCM.

    TODO: switch to PVPositioner subclass and override code that prevents
    loading, and make the wait for done just compare the values.
    """
    setpoint = Cpt(EpicsSignal, ":POSITIONSET")
    readback = Cpt(EpicsSignalRO, ":POSITIONGET", kind='hinted')

    limits = None


class CCMCalc(PseudoPositioner, FltMvInterface):
    """
    CCM calculation motors to move in terms of physics quantities

    All new parameters are scientific constants, and the current docstring
    writer is not familiar with all of them, so I will omit the full
    description instead of giving a partial and possibly incorrect summary.
    """
    energy = Cpt(PseudoSingleInterface, egu='keV', kind='hinted')
    wavelength = Cpt(PseudoSingleInterface, egu='A')
    theta = Cpt(PseudoSingleInterface, egu='deg')
    alio = Cpt(CCMMotor)

    tab_component_names = True

    def __init__(self, *args, theta0=default_theta0, dspacing=default_dspacing,
                 gr=default_gr, gd=default_gd, **kwargs):
        super().__init__(*args, auto_target=False, **kwargs)
        self.theta0 = theta0
        self.dspacing = dspacing
        self.gr = gr
        self.gd = gd

    def forward(self, pseudo_pos):
        """
        Take energy, wavelength, or theta and map to alio
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        # Figure out which one changed.
        energy, wavelength, theta = None, None, None
        if not np.isclose(pseudo_pos.energy, self.energy.position):
            energy = pseudo_pos.energy
        elif not np.isclose(pseudo_pos.wavelength, self.wavelength.position):
            wavelength = pseudo_pos.wavelength
        elif not np.isclose(pseudo_pos.theta, self.theta.position):
            theta = pseudo_pos.theta
        else:
            alio = self.alio.position
        logger.debug((energy, wavelength, theta))
        if energy is not None:
            wavelength = energy_to_wavelength(energy)
        if wavelength is not None:
            theta = wavelength_to_theta(wavelength, self.dspacing) * 180/np.pi
        if theta is not None:
            alio = theta_to_alio(theta * np.pi/180, self.theta0,
                                 self.gr, self.gd)
        return self.RealPosition(alio=alio)

    def inverse(self, real_pos):
        """
        Take alio and map to energy, wavelength, and theta
        """
        real_pos = self.RealPosition(*real_pos)
        theta = alio_to_theta(real_pos.alio, self.theta0, self.gr, self.gd)
        wavelength = theta_to_wavelength(theta, self.dspacing)
        energy = wavelength_to_energy(wavelength)
        return self.PseudoPosition(energy=energy,
                                   wavelength=wavelength,
                                   theta=theta*180/np.pi)


class CCMX(SyncAxesBase):
    """
    Combined motion of the CCM X motors
    """
    down = FCpt(IMS, '{self.down_prefix}')
    up = FCpt(IMS, '{self.up_prefix}')

    tab_component_names = True

    def __init__(self, down_prefix, up_prefix, *args, **kwargs):
        self.down_prefix = down_prefix
        self.up_prefix = up_prefix
        super().__init__(down_prefix, *args, **kwargs)


class CCMY(SyncAxesBase):
    """
    Combined motion of the CCM Y motors
    """
    down = FCpt(IMS, '{self.down_prefix}')
    up_north = FCpt(IMS, '{self.up_north_prefix}')
    up_south = FCpt(IMS, '{self.up_south_prefix}')

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
    theta2fine = FCpt(CCMMotor, '{self.theta2fine_prefix}')
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

    def __init__(self, alio_prefix, theta2fine_prefix, x_down_prefix,
                 x_up_prefix, y_down_prefix, y_up_north_prefix,
                 y_up_south_prefix, in_pos, out_pos, *args, **kwargs):
        self.alio_prefix = alio_prefix
        self.theta2fine_prefix = theta2fine_prefix
        self.x_down_prefix = x_down_prefix
        self.x_up_prefix = x_up_prefix
        self.y_down_prefix = y_down_prefix
        self.y_up_north_prefix = y_up_north_prefix
        self.y_up_south_prefix = y_up_south_prefix
        self._in_pos = in_pos
        self._out_pos = out_pos
        super().__init__(alio_prefix, *args, **kwargs)

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
    Converts theta angle (rad) to alio position (mm)
    """
    return gr * (1/np.cos(theta)-1) + gd * np.tan(theta - theta0)


def alio_to_theta(alio, theta0, gr, gd):
    """
    Converts alio position (mm) to theta angle (rad)

    This is an empirical inversion via binary search. If you decide to spend
    time trying to find the analytic solution here, please update this
    docstring, either to indicate your success or to increment the hours
    counter below.

    total hours spent here: 2
    """
    low = -1.0
    high = 1.0
    timeout = 1.0
    start = time.time()
    while time.time() - start < timeout:
        theta_guess = (low+high)/2
        alio_calc = theta_to_alio(theta_guess, theta0, gr, gd)
        if np.isclose(alio, alio_calc):
            break
        elif alio_calc > alio:
            high = theta_guess
        else:
            low = theta_guess
    return theta_guess


def wavelength_to_theta(wavelength, dspacing):
    """
    Converts wavelength (A) to theta angle (rad)
    """
    return np.arcsin(wavelength/2/dspacing)


def theta_to_wavelength(theta, dspacing):
    """
    Converts theta angle (rad) to wavelength (A)
    """
    return 2*dspacing*np.sin(theta)


def energy_to_wavelength(energy):
    """
    Converts photon energy (keV) to wavelength (A)
    """
    return 12.39842/energy


def wavelength_to_energy(wavelength):
    """
    Converts wavelength (A) to photon energy (keV)
    """
    return 12.39842/wavelength
