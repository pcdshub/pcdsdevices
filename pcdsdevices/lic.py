from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathInOutMixin
from .pmps import TwinCATStatePMPS


class LICMirror(TwinCATStatePMPS):
    """
    Standard TwinCATStatePMPS motion.

    The LICMirror does not block beam while at a mirror state.
    This is because it has a hole in the middle of the mirror for the
    x-ray beam to travel through.
    """
    _transmission = {
        'MIRROR1': 1,
        'MIRROR2': 1,
    }


class LaserInCoupling(BaseInterface, Device, LightpathInOutMixin):
    """
    Device to bring the optical laser to the sample via mirrors.
    """
    tab_component_names = True

    lightpath_cpts = ['mirror']
    _icon = 'fa.dot-circle-o'

    mirror = Cpt(LICMirror, ':MMS:STATE', kind='hinted',
                 doc='Control of the mirror via saved positions.')
    y_motor = Cpt(BeckhoffAxisNoOffset, ':MMS', kind='normal',
                  doc='Direct control of the mirror motor.')
