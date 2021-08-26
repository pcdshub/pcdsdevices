import logging
import typing
from collections import namedtuple

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.ophydobj import OphydObject
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from ophyd.status import MoveStatus

from .beam_stats import BeamEnergyRequest
from .device import GroupDevice
from .device import UnrelatedComponent as UCpt
from .epics_motor import IMS, EpicsMotorInterface
from .interface import BaseInterface, FltMvInterface, LightpathMixin
from .pseudopos import (PseudoPositioner, PseudoSingleInterface, SyncAxis,
                        SyncAxisOffsetMode)
from .pv_positioner import PVPositionerIsClose
from .utils import get_status_float

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


class CCMAlio(CCMMotor):
    cmd_home = Cpt(EpicsSignal, ':ENABLEPLC11', kind='omitted')
    cmd_kill = Cpt(EpicsSignal, ':KILL', kind='omitted')

    def home(self) -> None:
        """
        Finds the reference used for the Alio's position.

        Same as pressing "HOME" in the edm screen.
        """
        self.cmd_home.put(1)

    def kill(self) -> None:
        """
        Terminates the motion PID

        Same as pressing "KILL" in the edm screen.
        """
        self.cmd_kill.put(1)


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


class CCMEnergy(FltMvInterface, PseudoPositioner):
    """
    CCM energy motor.

    Calculated the current CCM energy using the alio position, and
    requests moves to the alio based on energy requests.

    Presents itself like a motor.
    """
    # Pseudo motor and real motor
    energy = Cpt(PseudoSingleInterface, egu='keV', kind='hinted',
                 limits=(4, 25), verbose_name='CCM Photon Energy')
    alio = Cpt(CCMAlio, '', kind='normal')

    # Calculation intermediates
    theta_deg = Cpt(Signal, kind='normal')
    wavelength = Cpt(Signal, kind='normal')
    resolution = Cpt(Signal, kind='normal')

    tab_component_names = True

    def __init__(self, prefix: str,
                 theta0: float = default_theta0,
                 dspacing: float = default_dspacing,
                 gr: float = default_gr,
                 gd: float = default_gd,
                 **kwargs):
        self.theta0 = theta0
        self.dspacing = dspacing
        self.gr = gr
        self.gd = gd
        super().__init__(prefix, auto_target=False, **kwargs)

    @alio.sub_default
    def _update_intermediates(self, value=None, **kwargs):
        """
        Update the calculation intermediates when the alio position updates.
        """
        if value is None:
            return
        theta = alio_to_theta(value, self.theta0, self.gr, self.gd)
        wavelength = theta_to_wavelength(theta, self.dspacing)
        self.theta_deg.put(theta * 180/np.pi)
        self.wavelength.put(wavelength)

        res_delta = 1e-4
        ref1 = self.alio_to_energy(value - res_delta/2)
        ref2 = self.alio_to_energy(value + res_delta/2)
        self.resolution.put(abs((ref1 - ref2) / res_delta))

    def forward(self, pseudo_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the setpoint.

        Converts the requested energy to the real position of the alio.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        energy = pseudo_pos.energy
        alio = self.energy_to_alio(energy)
        return self.RealPosition(alio=alio)

    def inverse(self, real_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the readback.

        Converts the real position of the alio to the calculated energy.
        """
        real_pos = self.RealPosition(*real_pos)
        alio = real_pos.alio
        energy = self.alio_to_energy(alio)
        return self.PseudoPosition(energy=energy)

    def energy_to_alio(self, energy: float) -> float:
        """
        Converts energy to alio.

        Parameters
        ----------
        energy : float
            The photon energy (color) in keV.

        Returns
        -------
        alio : float
            The alio position in mm
        """
        wavelength = energy_to_wavelength(energy)
        theta = wavelength_to_theta(wavelength, self.dspacing) * 180/np.pi
        alio = theta_to_alio(theta * np.pi/180, self.theta0, self.gr, self.gd)
        return alio

    def alio_to_energy(self, alio: float) -> float:
        """
        Converts alio to energy.

        Parameters
        ----------
        alio : float
            The alio position in mm

        Returns
        -------
        energy : float
            The photon energy (color) in keV.
        """
        theta = alio_to_theta(alio, self.theta0, self.gr, self.gd)
        wavelength = theta_to_wavelength(theta, self.dspacing)
        energy = wavelength_to_energy(wavelength)
        return energy


class CCMEnergyWithVernier(CCMEnergy):
    """
    CCM energy motor and the vernier.

    Moves the alio based on the requested energy using the values
    of the calculation constants, and reports the current energy
    based on the alio's position.

    Also moves the vernier when a move is requested to the alio.
    Note that the vernier is in units of eV, while the energy
    calculations are in units of keV.
    """
    vernier = FCpt(BeamEnergyRequest, '{hutch}', kind='normal')

    def __init__(self, prefix: str, hutch: str = None, **kwargs):
        # Put some effort into filling this automatically
        # CCM exists only in two hutches
        if hutch is not None:
            self.hutch = hutch
        elif 'XPP' in prefix:
            self.hutch = 'XPP'
        elif 'XCS' in prefix:
            self.hutch = 'XCS'
        else:
            self.hutch = 'TST'
        super().__init__(prefix, **kwargs)

    def forward(self, pseudo_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the setpoint.

        Converts the requested energy to the real position of the alio,
        and also converts that energy to eV and passes it along to
        the vernier.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        energy = pseudo_pos.energy
        alio = self.energy_to_alio(energy)
        vernier = energy * 1000
        return self.RealPosition(alio=alio, vernier=vernier)

    def inverse(self, real_pos: namedtuple) -> namedtuple:
        """
        PseudoPositioner interface function for calculating the readback.

        Converts the real position of the alio to the calculated energy
        """
        real_pos = self.RealPosition(*real_pos)
        alio = real_pos.alio
        energy = self.alio_to_energy(alio)
        return self.PseudoPosition(energy=energy)


class CCMX(SyncAxis):
    """Combined motion of the CCM X motors."""
    down = UCpt(IMS, kind='normal')
    up = UCpt(IMS, kind='normal')

    offset_mode = SyncAxisOffsetMode.STATIC_FIXED
    tab_component_names = True

    def __init__(self, prefix: str = None, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        prefix = prefix or self.unrelated_prefixes['down_prefix']
        super().__init__(prefix, **kwargs)


class CCMY(SyncAxis):
    """Combined motion of the CCM Y motors."""
    down = UCpt(IMS, kind='normal')
    up_north = UCpt(IMS, kind='normal')
    up_south = UCpt(IMS, kind='normal')

    offset_mode = SyncAxisOffsetMode.STATIC_FIXED
    tab_component_names = True

    def __init__(self, prefix: str = None, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        prefix = prefix or self.unrelated_prefixes['down_prefix']
        super().__init__(prefix, **kwargs)


class CCM(BaseInterface, GroupDevice, LightpathMixin):
    """
    The full CCM assembly.

    This requires a huge number of motor pv prefixes to be passed in, and they
    are all labelled accordingly.
    """
    energy = Cpt(CCMEnergy, '', kind='hinted')
    energy_with_vernier = Cpt(CCMEnergyWithVernier, '', kind='normal')

    alio = UCpt(CCMAlio, kind='normal')
    theta2fine = UCpt(CCMMotor, atol=0.01, kind='normal')
    theta2coarse = UCpt(CCMPico, kind='normal')
    chi2 = UCpt(CCMPico, kind='normal')
    x = UCpt(CCMX, add_prefix=[], kind='normal')
    y = UCpt(CCMY, add_prefix=[], kind='normal')

    lightpath_cpts = ['x']
    tab_component_names = True
    tab_whitelist = ['x1', 'x2', 'y1', 'y2', 'y3', 'E', 'E_vernier',
                     'th2coarse', 'th2fine', 'alio2E', 'E2alio',
                     'home', 'kill', 'status',
                     'insert', 'remove', 'inserted', 'removed']

    def __init__(self, *, prefix: str = None, in_pos: float, out_pos: float,
                 theta0: float = default_theta0,
                 dspacing: float = default_dspacing,
                 gr: float = default_gr,
                 gd: float = default_gd,
                 **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        self._in_pos = in_pos
        self._out_pos = out_pos
        prefix = prefix or self.unrelated_prefixes['alio_prefix']
        super().__init__(prefix, **kwargs)
        self.theta0 = theta0
        self.dspacing = dspacing
        self.gr = gr
        self.gd = gd

        # Aliases: defined by the scientists
        self.x1 = self.x.down
        self.x2 = self.x.up
        self.y1 = self.y.down
        self.y2 = self.y.up_north
        self.y3 = self.y.up_south
        # TODO investigate request for set_current_position on ccm.E to
        # reset the offset values used for alio/energy conversion
        self.E = self.energy.energy
        self.E_vernier = self.energy_with_vernier.energy
        self.th2coarse = self.theta2coarse
        self.th2fine = self.theta2fine
        self.alio2E = self.energy.alio_to_energy
        self.E2alio = self.energy.energy_to_alio
        self.home = self.alio.home
        self.kill = self.alio.kill

    def status(self) -> str:
        """
        Returns a str with the current pv values for the device.
        """
        return self.format_status_info(self.status_info())

    def format_status_info(self, status_info: dict[str, typing.Any]) -> str:
        """
        Define how we're going to format the state of the CCM for the user.
        """
        # Pull out the numbers we want and format them, or show N/A if failed
        alio = get_status_float(status_info, 'alio', 'position', precision=4)
        theta = get_status_float(status_info, 'energy', 'theta_deg', 'value',
                                 precision=3)
        wavelength = get_status_float(status_info, 'energy', 'wavelength',
                                      'value', precision=4)
        energy = get_status_float(status_info, 'energy', 'energy', 'position',
                                  precision=4)
        res_mm = get_status_float(status_info, 'energy', 'resolution', 'value',
                                  scale=1e3, precision=1)
        res_um = get_status_float(status_info, 'energy', 'resolution', 'value',
                                  precision=2)
        x_down = get_status_float(status_info, 'x', 'down', 'position',
                                  precision=3)
        x_up = get_status_float(status_info, 'x', 'up', 'position',
                                precision=3)
        try:
            xavg = np.average([float(x_down), float(x_up)])
            xavg = f'{xavg:.3f}'
        except TypeError:
            xavg = 'N/A'

        # Fill out the text
        text = f'alio   (mm): {alio}\n'
        text += f'angle (deg): {theta}\n'
        text += f'lambda  (A): {wavelength}\n'
        text += f'Energy (keV): {energy}\n'
        text += f'res (eV/mm): {res_mm}\n'
        text += f'res (eV/um): {res_um}\n'
        text += f'x @ (mm): {xavg} [x1,x2={x_down},{x_up}]\n'
        return text

    @property
    def theta0(self) -> float:
        """
        The calculation constant theta0 for the alio <-> energy calc.

        This seems to be a reference angle for the calculation.
        """
        return self._theta0

    @theta0.setter
    def theta0(self, value: float):
        self.energy.theta0 = value
        self.energy_with_vernier.theta0 = value
        self._theta0 = value

    @property
    def dspacing(self) -> float:
        """
        The calculation constant dspacing for the alio <-> energy calc.

        This seems to be information about the crystal lattice.
        """
        return self._dspacing

    @dspacing.setter
    def dspacing(self, value: float):
        self.energy.dspacing = value
        self.energy_with_vernier.dspacing = value
        self._dspacing = value

    @property
    def gr(self) -> float:
        """
        The calculation constant gr for the alio <-> energy calc.

        I'm not sure what this actually is geometrically.
        """
        return self._gr

    @gr.setter
    def gr(self, value: float):
        self.energy.gr = value
        self.energy_with_vernier.gr = value
        self._gr = value

    @property
    def gd(self) -> float:
        """
        The calculation constant gd for the alio <-> energy calc.

        I'm not sure what this actually is geometrically.
        """
        return self._gd

    @gd.setter
    def gd(self, value: float):
        self.energy.gd = value
        self.energy_with_vernier.gd = value
        self._gd = value

    def _set_lightpath_states(
            self,
            lightpath_values: dict[OphydObject, dict[str, typing.Any]],
            ) -> None:
        """
        Update the fields used by the lightpath to determine in/out.

        Compares the x position with the saved in and out values.
        """
        x_pos = lightpath_values[self.x]['value']
        self._inserted = np.isclose(x_pos, self._in_pos)
        self._removed = np.isclose(x_pos, self._out_pos)
        if self._removed:
            self._transmission = 1
        else:
            # Placeholder "small attenuation" value
            self._transmission = 0.9

    def insert(self, wait: bool = False) -> MoveStatus:
        """
        Move the x motors to the saved "in" position.
        """
        return self.x.move(self._in_pos, wait=wait)

    def remove(self, wait: bool = False) -> MoveStatus:
        """
        Move the x motors to the saved "out" position.
        """
        return self.x.move(self._out_pos, wait=wait)


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
