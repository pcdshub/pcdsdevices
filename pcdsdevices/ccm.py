import time

import numpy as np
from ophyd.device import Component as Cpt, FormattedComponent as FCpt
from ophyd.pseudopos import PseudoPositioner, PseudoSingle
from ophyd.pv_positioner import PVPositionerPC
from ophyd.signal import EpicsSignal, EpicsSignalRO, AttributeSignal

from .epics_motor import IMS
from .inout import InOutPositioner
from .pseudopos import SyncAxesBase


# Default constants copied verbatim from old python
gTheta0 = 14.9792 * np.pi/180
gSi111dspacing = 3.1356011499587773
gSi511dspacing = 1.0452003833195924
gdspacing = gSi111dspacing
gR = 3.175
gD = 231.303


# Calculations between alio position and energy, with all intermediates.
def theta_to_alio(theta, gTheta0, gR, gD):
    """
    Converts theta angle (rad) to alio position (mm)
    """
    return gR * (1/np.cos(theta)-1) + gD * np.tan(theta - gTheta0)


def alio_to_theta(alio, gTheta0, gR, gD):
    """
    Converts alio position (mm) to theta angle (rad)
    """
    low = -1.0
    high = 1.0
    timeout = 1.0
    start = time.time()
    while time.time() - start < timeout:
        theta_guess = (low+high)/2
        alio_calc = theta_to_alio(theta_guess, gTheta0, gR, gD)
        if np.isclose(alio, alio_calc):
            break
        elif alio_calc > alio:
            high = theta_guess
        else:
            low = theta_guess
    return theta_guess


def wavelength_to_theta(wavelength, gdspacing):
    """
    Converts wavelength (A) to theta angle (rad)
    """
    return np.arcsin(wavelength/2/gdspacing)


def theta_to_wavelength(theta, gdspacing):
    """
    Converts theta angle (rad) to wavelength (A)
    """
    return 2*gdspacing*np.sin(theta)


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


# Auxilliary classes
class CCMMotor(PVPositionerPC):
    """
    Goofy records used in the CCM.

    TODO: switch to PVPositioner subclass and override code that prevents
    loading, and make the wait for done just compare the values.
    """
    setpoint = Cpt(EpicsSignal, ":POSITIONSET")
    readback = Cpt(EpicsSignalRO, ":POSITIONGET")


class CCMCalc(PseudoPositioner):
    """
    CCM calculation motors to move in terms of physics quantities
    """
    energy = Cpt(PseudoSingle, egu='keV', kind='hinted')
    wavelength = Cpt(PseudoSingle, egu='A')
    theta = Cpt(PseudoSingle, egu='deg')
    alio = Cpt(CCMMotor)

    def __init__(self, *args, gTheta0=gTheta0, gdspacing=gdspacing,
                 gR=gR, gD=gD, **kwargs):
        super().__init__(*args, **kwargs)
        self.gTheta0 = gTheta0
        self.gdspacing = gdspacing
        self.gR = gR
        self.gD = gD

    def forward(self, pseudo_pos):
        """
        Take energy, wavelength, or theta and map to alio
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        # Figure out which one changed.
        energy, wavelength, theta = None, None, None
        if pseudo_pos.energy != self.energy.position:
            energy = pseudo_pos.energy
        elif pseudo_pos.wavelenth != self.wavelength.position:
            wavelength = pseudo_pos.wavelength
        elif pseudo_pos.theta*np.pi/180 != self.theta.position:
            theta = pseudo_pos.theta*np.pi/180
        else:
            alio = self.alio.position
        if energy is not None:
            wavelength = energy_to_wavelength(energy)
        if wavelength is not None:
            theta = wavelength_to_theta(wavelength, self.gdspacing)
        if theta is not None:
            alio = theta_to_alio(theta, self.gTheta0, self.gR, self.gD)
        return self.RealPosition(alio=alio)

    def inverse(self, real_pos):
        """
        Take alio and map to energy, wavelength, and theta
        """
        real_pos = self.RealPosition(*real_pos)
        theta = alio_to_theta(real_pos.alio, self.gTheta0, self.gR, self.gD)
        wavelength = theta_to_wavelength(theta, self.gdspacing)
        energy = wavelength_to_energy(wavelength)
        return self.PseudoPosition(energy=energy,
                                   wavelength=wavelength,
                                   theta=theta*180/np.pi)


class CCMX(SyncAxesBase):
    """
    Combined motion of the CCM X motors
    """
    down = FCpt(IMS, '{self._down}')
    up = FCpt(IMS, '{self._up}')

    def __init__(self, *args, parent, **kwargs):
        self._down = parent._x_down_prefix
        self._up = parent._x_up_prefix
        super().__init__(*args, parent=parent, **kwargs)


class CCMY(SyncAxesBase):
    """
    Combined motion of the CCM Y motors
    """
    down = FCpt(IMS, '{self._down}')
    up_north = FCpt(IMS, '{self._up_north')
    up_south = FCpt(IMS, '{self._up_south')

    def __init__(self, *args, parent, **kwargs):
        self._down = parent._y_down_prefix
        self._up_north = parent._y_up_north_prefix
        self._up_south = parent._y_up_south_prefix
        super().__init__(*args, parent=parent, **kwargs)


# Main Class
class CCM(InOutPositioner):
    calc = FCpt(CCMCalc, "{self._alio_prefix}", kind='hinted')
    theta2fine = FCpt(CCMMotor, "{self._th2f_prefix}")
    x = Cpt(CCMX)
    y = Cpt(CCMY)
    state = Cpt(AttributeSignal, '_state', kind='hinted')

    # Placeholder value. This represents "not full transmission".
    _transmission = {'IN': 0.9}

    def __init__(self, x_down, x_up, y_down, y_up_north, y_up_south, alio,
                 theta2fine, inpos, outpos, **kwargs):
        self._x_down_prefix = x_down
        self._x_up_prefix = x_up
        self._y_down_prefix = y_down
        self._y_up_north_prefix = y_up_north
        self._y_up_south_prefix = y_up_south
        self._alio_prefix = alio
        self._th2f_prefix = theta2fine
        self._inpos = inpos
        self._outpos = outpos
        super().__init__(prefix='', **kwargs)

    @property
    def _state(self):
        if np.isclose(self.x.position, self._inpos):
            return 1
        elif np.isclose(self.x.position, self._outpos):
            return 2
        else:
            return 0

    @_state.setter
    def _state(self, value):
        if value == 1:
            self.x.move(self._inpos)
        elif value == 2:
            self.x.move(self._outpos)
