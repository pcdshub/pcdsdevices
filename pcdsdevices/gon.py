"""
Module for goniometers and sample stages used with them.
"""
from ophyd import Device
from ophyd import FormattedComponent as FCpt

from .epics_motor import IMS
from .interface import BaseInterface


class BaseGon(Device, BaseInterface):
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
                 **kwargs):
        self._prefix_2theta = prefix_2theta
        self._prefix_dettilt = prefix_dettilt
        self._prefix_detver = prefix_detver
        super().__init__(name=name, **kwargs)


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


class XYZStage(Device, BaseInterface):
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


class SamPhi(Device, BaseInterface):
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


class Kappa(Device, BaseInterface):
    """
    Kappa stage.

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
    """

    x = FCpt(IMS, '{self._prefix_x}', kind='normal')
    y = FCpt(IMS, '{self._prefix_y}', kind='normal')
    z = FCpt(IMS, '{self._prefix_z}', kind='normal')
    eta = FCpt(IMS, '{self._prefix_eta}', kind='normal')
    kappa = FCpt(IMS, '{self._prefix_kappa}', kind='normal')
    phi = FCpt(IMS, '{self._prefix_phi}', kind='normal')

    tab_component_names = True

    def __init__(self, *, name, prefix_x, prefix_y, prefix_z, prefix_eta,
                 prefix_kappa, prefix_phi, **kwargs):
        self._prefix_x = prefix_x
        self._prefix_y = prefix_y
        self._prefix_z = prefix_z
        self._prefix_eta = prefix_eta
        self._prefix_kappa = prefix_kappa
        self._prefix_phi = prefix_phi
        super().__init__('', name=name, **kwargs)
