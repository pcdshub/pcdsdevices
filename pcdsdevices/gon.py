"""
Module for goniometers and sample stages used with them.
"""
import logging

import numpy as np
from ophyd import FormattedComponent as FCpt
from ophyd.device import Component as Cpt
from ophyd.status import DeviceStatus
from prettytable import PrettyTable

from .device import GroupDevice
from .epics_motor import IMS
from .interface import BaseInterface
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)
from .sim import FastMotor
from .utils import get_status_float, get_status_value

logger = logging.getLogger(__name__)


class BaseGon(BaseInterface, GroupDevice):
    """
    Basic goniometer, as present in XPP.

    This requires eight motor PV prefixes to be passed in as keyword
    arguments, and they are all labelled accordingly.

    Parameters
    ----------
    name : str
        A name to refer to the goniometer device.

    prefix_hor : str
        The EPICS base PV of the common-horizontal motor.

    prefix_ver : str
        The EPICS base PV of the common-vertical motor.

    prefix_rot : str
        The EPICS base PV of the common-rotation motor.

    prefix_tip : str
        The EPICS base PV of the sample-stage's tip motor.

    prefix_tilt : str
        The EPICS base PV of the sample-stage's tilt motor.
    """

    hor = FCpt(IMS, '{self._prefix_hor}', kind='normal')
    ver = FCpt(IMS, '{self._prefix_ver}', kind='normal')
    rot = FCpt(IMS, '{self._prefix_rot}', kind='normal')
    tip = FCpt(IMS, '{self._prefix_tip}', kind='normal')
    tilt = FCpt(IMS, '{self._prefix_tilt}', kind='normal')

    tab_component_names = True

    def __init__(self, *, name, prefix_hor, prefix_ver, prefix_rot, prefix_tip,
                 prefix_tilt, **kwargs):
        self._prefix_hor = prefix_hor
        self._prefix_ver = prefix_ver
        self._prefix_rot = prefix_rot
        self._prefix_tip = prefix_tip
        self._prefix_tilt = prefix_tilt
        super().__init__('', name=name, **kwargs)

    def format_status_info(self, status_info):
        """
        Override status info handler to render the xpp goniometer.

        Display xpp goniometer status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        horiz = get_status_float(status_info, 'hor', 'position')
        vert = get_status_float(status_info, 'ver', 'position')
        units = get_status_value(status_info, 'hor', 'user_setpoint', 'units')

        rot = get_status_float(status_info, 'rot', 'position')
        tip = get_status_float(status_info, 'tip', 'position')
        tilt = get_status_float(status_info, 'tilt', 'position')
        angle_units = get_status_value(status_info, 'rot', 'user_setpoint',
                                       'units')

        return f"""\
XPP Goniometer
H, V: {horiz}, {vert} [{units}]
Theta, Pitch, Roll: {rot}, {tilt}, {tip} [{angle_units}]
"""


class GonWithDetArm(BaseGon):
    """
    Goniometer with a detector arm, as present in XCS.

    This requires eleven motor PV prefixes to be passed in as keyword
    arguments, and they are all labelled accordingly.

    Parameters
    ----------
    name : str
        A name to refer to the goniometer device.

    prefix_hor : str
        The EPICS base PV of the common-horizontal motor.

    prefix_ver : str
        The EPICS base PV of the common-vertical motor.

    prefix_rot : str
        The EPICS base PV of the common-rotation motor.

    prefix_tip : str
        The EPICS base PV of the sample-stage's tip motor.

    prefix_tilt : str
        The EPICS base PV of the sample-stage's tilt motor.

    prefix_2theta : str
        The EPICS base PV of the detector arm's 2theta rotation motor.

    prefix_dettilt : str
        The EPICS base PV of the detector stage's tilt motor.

    prefix_detver : str
        The EPICS base PV of the detector stage's vertical motor.
    """

    rot_2theta = FCpt(IMS, '{self._prefix_2theta}', kind='normal')
    det_tilt = FCpt(IMS, '{self._prefix_dettilt}', kind='normal')
    det_ver = FCpt(IMS, '{self._prefix_detver}', kind='normal')

    def __init__(self, *, name, prefix_2theta, prefix_dettilt, prefix_detver,
                 prefix_hor, prefix_ver, prefix_rot, prefix_tip, prefix_tilt,
                 **kwargs):
        self._prefix_2theta = prefix_2theta
        self._prefix_dettilt = prefix_dettilt
        self._prefix_detver = prefix_detver
        super().__init__(name=name, prefix_hor=prefix_hor,
                         prefix_ver=prefix_ver, prefix_rot=prefix_rot,
                         prefix_tip=prefix_tip, prefix_tilt=prefix_tilt,
                         **kwargs)


def Goniometer(**kwargs):
    """
    Factory function for Goniometers.

    Returns either a :class:`BaseGon` or :class:`GonWithDetArm` class,
    depending on which prefixes are given.

    This requires either eight or eleven motor PV prefixes, depending on the
    type of goniometer being used, to be passed in as keyword arguments, and
    they are all labelled accordingly.

    Parameters
    ----------
    name : str
        A name to refer to the goniometer device.

    prefix_hor : str
        The EPICS base PV of the common-horizontal motor.

    prefix_ver : str
        The EPICS base PV of the common-vertical motor.

    prefix_rot : str
        The EPICS base PV of the common-rotation motor.

    prefix_tip : str
        The EPICS base PV of the sample-stage's tip motor.

    prefix_tilt : str
        The EPICS base PV of the sample-stage's tilt motor.

    prefix_2theta : str, optional
        The EPICS base PV of the detector arm's 2theta rotation motor.

    prefix_dettilt : str, optional
        The EPICS base PV of the detector stage's tilt motor.

    prefix_detver : str, optional
        The EPICS base PV of the detector stage's vertical motor.
    """

    if all(x in kwargs for x in ['prefix_2theta', 'prefix_dettilt',
                                 'prefix_detver']):
        return GonWithDetArm(**kwargs)
    else:
        return BaseGon(**kwargs)


class XYZStage(BaseInterface, GroupDevice):
    """
    Sample XYZ stage.

    Parameters
    ----------
    name : str
        A name to refer to the device

    prefix_x : str
        The EPICS base PV of the sample-stage's x motor.

    prefix_y : str
        The EPICS base PV of the sample-stage's y motor.

    prefix_z : str
        The EPICS base PV of the sample-stage's z motor.
    """

    x = FCpt(IMS, '{self._prefix_x}', kind='normal')
    y = FCpt(IMS, '{self._prefix_y}', kind='normal')
    z = FCpt(IMS, '{self._prefix_z}', kind='normal')

    tab_component_names = True

    def __init__(self, *, name, prefix_x, prefix_y, prefix_z, **kwargs):
        self._prefix_x = prefix_x
        self._prefix_y = prefix_y
        self._prefix_z = prefix_z
        super().__init__('', name=name, **kwargs)

    def format_status_info(self, status_info):
        """Override status info handler to render the `XYZStage`."""
        x = get_status_float(status_info, 'x', 'position')
        y = get_status_float(status_info, 'y', 'position')
        z = get_status_float(status_info, 'z', 'position')
        units = get_status_value(status_info, 'x', 'user_setpoint', 'units')

        return f"""\
XYZStage
X, Y, Z: {x}, {y}, {z} [{units}]
"""


class KappaXYZStage(XYZStage):
    """Helper initializing function for XYZStage object."""
    def __init__(self, *args, parent, **kwargs):
        self._prefix_x = parent._prefix_x
        self._prefix_y = parent._prefix_y
        self._prefix_z = parent._prefix_z
        super().__init__(*args, parent=parent, prefix_x=self._prefix_x,
                         prefix_y=self._prefix_y, prefix_z=self._prefix_z,
                         **kwargs)


class SamPhi(BaseInterface, GroupDevice):
    """
    Sample Phi stage.

    Parameters
    ----------
    name : str
        A name to refer to the Sample Phi stage device.

    prefix_samz : str
        The EPICS base PV of the Sample Phi stage's z motor.

    prefix_samphi : str
        The EPICS base PV of the Sample Phi stage's phi motor.
    """

    sam_z = FCpt(IMS, '{self._prefix_samz}', kind='normal')
    sam_phi = FCpt(IMS, '{self._prefix_samphi}', kind='normal')

    tab_component_names = True

    def __init__(self, *, name, prefix_samz, prefix_samphi, **kwargs):
        self._prefix_samz = prefix_samz
        self._prefix_samphi = prefix_samphi
        super().__init__('', name=name, **kwargs)


class KappaMoveAbort(ValueError):
    """Exception raised when the user aborts a Kappa move."""
    pass


class Kappa(BaseInterface, PseudoPositioner, GroupDevice):
    """
    Kappa stage, control the Kappa diffractometer in spherical coordinates.

    The kappa's native coordinates (eta, kappa, phi) are mechanically
    convenient, but geometrically awkward to think about. This module
    replaces the coordinates with (e_eta, e_chi, e_phi) like so:

    The radial component is generally fixed such that the sample is at
    the center of rotation, but you may think of `z` as the radial
    component (inverted because the sample is pushed into the center of the
    coordinate system, rather than out from the center.)

    Parameters
    ----------
    name : str
        A name to refer to the Kappa stage device.

    prefix_x : str
        The EPICS base PV of the Kappa stage's x motor.

    prefix_y : str
        The EPICS base PV of the Kappa stage's y motor.

    prefix_z : str
        The EPICS base PV of the Kappa stage's z motor.

    prefix_eta : str
        The EPICS base PV of the Kappa stage's eta motor.

    prefix_kappa : str
        The EPICS base PV of the Kappa stage's kappa motor.

    prefix_phi : str
        The EPICS base PV of the Kappa stage's phi motor.

    eta_max_step : int, optional
        Maximum eta motor step, the largest move eta motor can make without
        user's confirmation. Defaults to 2.

    kappa_max_step : int, optional
        Maximum kappa motor step, the largest move kappa motor can make
        without user's confirmation. Defaults to 2.

    phi_max_step : int, optional
        Maximum phi motor step, the largest move phi motor can make without
        user's confirmation. Defaults to 2.

    kappa_ang : number, optional
        The angle of the kappa motor relative to the eta motor, in degrees.
        Defaults to 50.

    Notes
    -----
    When using the Kappa, it is most convenient to work through the pseudo
    motors:

    `kappa.e_eta`
    `kappa.e_chi`
    `kappa.e_phi`

    Which have the normal motor functionalities (`mv`, `mvr`, `wm`).

    It may be helpful to scan these pseudo motors to find the optimal position,
    but make sure the step size is small enough so that you don't have to
    confirm motion on every step.

    Move commands will block the main thread, and pressing ctrl+c will cancel
    motion.

    The x, y, and z are the sample adjustment motors used to attain center of
    rotation
    """
    sample_stage = Cpt(KappaXYZStage, name='', kind='normal')

    # The real (or physical) positioners:
    eta = FCpt(IMS, '{self._prefix_eta}', kind='normal')
    kappa = FCpt(IMS, '{self._prefix_kappa}', kind='normal')
    phi = FCpt(IMS, '{self._prefix_phi}', kind='normal')
    # The pseudo positioner axes:
    e_eta = FCpt(PseudoSingleInterface, kind='normal', name='gon_kappa_e_eta')
    e_chi = FCpt(PseudoSingleInterface, kind='normal', name='gon_kappa_e_chi')
    e_phi = FCpt(PseudoSingleInterface, kind='normal', name='gon_kappa_e_phi')

    # Only stage the motors involved in the coordinate transform
    stage_group = [eta, kappa, phi]
    tab_component_names = True
    tab_whitelist = ['stop', 'wait', 'k_to_e', 'e_to_k', 'check_motor_step']

    def __init__(self, *, name, prefix_x, prefix_y, prefix_z,
                 prefix_eta, prefix_kappa, prefix_phi, eta_max_step=2,
                 kappa_max_step=2, phi_max_step=2, kappa_ang=50, **kwargs):
        self._prefix_x = prefix_x
        self._prefix_y = prefix_y
        self._prefix_z = prefix_z
        self._prefix_eta = prefix_eta
        self._prefix_kappa = prefix_kappa
        self._prefix_phi = prefix_phi
        self.eta_max_step = eta_max_step
        self.kappa_max_step = kappa_max_step
        self.phi_max_step = phi_max_step
        self.kappa_ang = kappa_ang
        super().__init__('', name=name, **kwargs)
        self.x = self.sample_stage.x
        self.y = self.sample_stage.y
        self.z = self.sample_stage.z

    def wait(self, timeout=None):
        """Block until the action completes."""
        self.eta.wait(timeout=timeout)
        self.kappa.wait(timeout=timeout)
        self.phi.wait(timeout=timeout)

    @property
    def e_eta_coord(self):
        """Get the azimuthal angle, an offset from eta."""
        e_eta, e_chi, e_phi = self.k_to_e()
        return e_eta

    @property
    def e_chi_coord(self):
        """Get the elevation (polar) angle, a composition of eta and kappa."""
        e_eta, e_chi, e_phi = self.k_to_e()
        return e_chi

    @property
    def e_phi_coord(self):
        """Get the sample rotation angle, an offset from phi to keep it."""
        e_eta, e_chi, e_phi = self.k_to_e()
        return e_phi

    def k_to_e(self, eta=None, kappa=None, phi=None):
        """
        Convert from native kappa coordinates to spherical coordinates.

        If a parameter is left as None, use the live value.

        Parameters
        ----------
        eta : number
            Eta motor position.
        kappa : number
            Kappa motor position.
        phi : number
            Phi motor position.

        Returns
        -------
        coordinates : tuple
            Spherical coordinates.
        """
        if eta is None:
            eta = self.eta.position
        if kappa is None:
            kappa = self.kappa.position
        if phi is None:
            phi = self.phi.position

        kappa_ang = self.kappa_ang * np.pi / 180
        delta = np.arctan(np.tan(kappa * np.pi / 180 / 2)
                          * np.cos(kappa_ang))

        e_eta = -eta * np.pi / 180 - delta
        e_chi = 2 * np.arcsin(np.sin(kappa * np.pi / 180 / 2)
                              * np.sin(kappa_ang))
        e_phi = -phi * np.pi / 180 - delta

        # Phase shift for flipped kappa
        if self.kappa.position > 180:
            e_eta = np.pi - e_eta
            e_chi = e_chi
            e_phi = phi * np.pi / 180 - delta

        e_eta = e_eta * 180 / np.pi
        e_chi = e_chi * 180 / np.pi
        e_phi = e_phi * 180 / np.pi
        return e_eta, e_chi, e_phi

    def e_to_k(self, e_eta=None, e_chi=None, e_phi=None):
        """
        Convert from spherical coordinates to the native kappa coordinates.

        If a parameter is left as None, use the live value.

        Parameters
        ----------
        e_eta : number
            e_eta pseudo motor's spherical coordinate
        e_chi : number
            e_chi pseudo motor's spherical coordinate
        e_phi : number
            e_phi pseudo motor's spherical coordinate

        Returns
        -------
        coordinates : tuple
            Native kappa coordinates.
        """
        if e_eta is None:
            e_eta = self.e_eta_coord
        if e_chi is None:
            e_chi = self.e_chi_coord
        if e_phi is None:
            e_phi = self.e_phi_coord

        kappa_ang = self.kappa_ang * np.pi / 180
        delta = np.arcsin(-np.tan(e_chi * np.pi / 180 / 2)
                          / np.tan(kappa_ang))
        k_eta = -(e_eta * np.pi / 180 - delta)
        k_kap = 2 * np.arcsin(np.sin(e_chi * np.pi / 180 / 2)
                              / np.sin(kappa_ang))
        k_phi = e_phi * np.pi / 180 - delta

        # Phase shift for flipped kappa
        if self.kappa.position > 180:
            k_eta = -k_eta - np.pi
            k_kap = 2 * np.pi - k_kap
            k_phi = -e_phi * np.pi / 180 - delta

        k_eta = k_eta * 180 / np.pi
        k_kap = k_kap * 180 / np.pi
        k_phi = -k_phi * 180 / np.pi
        return k_eta, k_kap, k_phi

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Calculate a RealPosition from a given PseudoPosition.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            The pseudo position input.
        Returns
        -------
        real_position : RealPosition
            The real position output.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        eta, kappa, phi = self.e_to_k(pseudo_pos.e_eta, pseudo_pos.e_chi,
                                      pseudo_pos.e_phi)
        return self.RealPosition(eta=eta, kappa=kappa, phi=phi)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Calculate a PseudoPosition from a given RealPosition.

        Parameters
        ----------
        real_position : RealPosition
            The real position input.
        Returns
        -------
        pseudo_pos : PseudoPosition
            The pseudo position output.
        """
        real_pos = self.RealPosition(*real_pos)
        e_eta, e_chi, e_phi = self.k_to_e(real_pos.eta, real_pos.kappa,
                                          real_pos.phi)
        return self.PseudoPosition(e_eta=e_eta, e_chi=e_chi, e_phi=e_phi)

    @pseudo_position_argument
    def move(self, position, wait=True, timeout=None, moved_cb=None):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Checks for the motor step, and ask the user for confirmation if
        movement step is greater than default one.
        """
        try:
            return super().move(position, wait=wait, timeout=timeout,
                                moved_cb=moved_cb)
        except KappaMoveAbort as exc:
            logger.warning('Aborting moving for safety.')
            status = DeviceStatus(self)
            status.set_exception(exc)
            return status

    def check_value(self, position):
        """
        Check the goal position and raise an exception if it is not safe.

        This is called before executing any move.
        """
        super().check_value(position)
        eta, kappa, phi = self.e_to_k(position.e_eta, position.e_chi,
                                      position.e_phi)
        if not self.check_motor_step(eta, kappa, phi):
            raise KappaMoveAbort('Unsafe Kappa move aborted!')

    def check_motor_step(self, eta, kappa, phi):
        """
        Check for the motor steps.

        Compare desired movement destinations with current positions. If any of
        the deltas are greater than their respective max step, ask the user for
        confirmation.

        Parameters
        ----------
        eta : number
            Desired eta destination position.
        kappa : number
            Desired kappa destination position.
        phi : number
            Desired phi destination position.

        Returns
        -------
        move_on : bool
           `True` if motor step is smaller than the respective max step and/or
           the user has confirmed yes.
        """
        eta_step = abs(eta - self.eta.position)
        kappa_step = abs(kappa - self.kappa.position)
        phi_step = abs(phi - self.phi.position)

        is_eta_above_max = eta_step > self.eta_max_step
        is_kappa_above_max = kappa_step > self.kappa_max_step
        is_phi_above_max = phi_step > self.phi_max_step

        if is_eta_above_max or is_kappa_above_max or is_phi_above_max:
            d_str = '\nDo you really intend to do the following motions?\n'
            t = PrettyTable(['Motor', 'Current position', 'to',
                             'Target position'])
            t.add_row(['eta', self.eta.position, '-->', eta])
            t.add_row(['kappa', self.kappa.position, '-->', kappa])
            t.add_row(['phi', self.phi.position, '-->', phi])
            e_eta, e_chi, e_phi = self.k_to_e(eta=eta, kappa=kappa, phi=phi)
            t.add_row(['e_eta', self.e_eta.position, '-->', e_eta])
            t.add_row(['e_chi', self.e_chi.position, '-->', e_chi])
            t.add_row(['e_phi', self.e_phi.position, '-->', e_phi])
            print(d_str, t)

            if input('  (y/n) ') == 'y':
                move_on = True
            else:
                move_on = False
        else:
            move_on = True
        return move_on

    def format_status_info(self, status_info):
        """Override status info handler to render the Kappa object."""
        x = get_status_float(status_info, 'sample_stage', 'x', 'position')
        y = get_status_float(status_info, 'sample_stage', 'y', 'position')
        z = get_status_float(status_info, 'sample_stage', 'z', 'position')
        units = get_status_value(status_info, 'sample_stage', 'x',
                                 'user_setpoint', 'units')

        eta = get_status_float(status_info, 'eta', 'position')
        kappa = get_status_float(status_info, 'kappa', 'position')
        phi = get_status_float(status_info, 'phi', 'position')
        angle_units = get_status_value(status_info, 'eta', 'user_setpoint',
                                       'units')
        e_eta = get_status_float(status_info, 'e_eta', 'position')
        e_chi = get_status_float(status_info, 'e_chi', 'position')
        e_phi = get_status_float(status_info, 'e_phi', 'position')

        return f"""\
Kappa
eta, kappa, phi: {eta}, {kappa}, {phi} [{angle_units}]
e_eta, e_chi, e_phi: {e_eta}, {e_chi}, {e_phi}
x, y, z: {x}, {y}, {z} [{units}]
"""


class SimSampleStage(KappaXYZStage):
    x = Cpt(FastMotor, limits=(-100, 100))
    y = Cpt(FastMotor, limits=(-100, 100))
    z = Cpt(FastMotor, limits=(-100, 100))


class SimKappa(Kappa):
    """Test version of the Kappa object."""
    sample_stage = Cpt(SimSampleStage, name='')
    eta = Cpt(FastMotor, limits=(-180, 180))
    kappa = Cpt(FastMotor, limits=(-360, 360))
    phi = Cpt(FastMotor, limits=(-180, 180))

    def __init__(self):
        super().__init__(name='SimKappa', prefix_x='X', prefix_y='Y',
                         prefix_z='Z', prefix_eta='ETA', prefix_kappa='KAPPA',
                         prefix_phi='PHI')
