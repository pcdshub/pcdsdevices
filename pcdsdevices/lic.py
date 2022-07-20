from ophyd import Component as Cpt

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathInOutCptMixin
from .pmps import TwinCATStatePMPS


class LICMirror(TwinCATStatePMPS):
    """
    Standard TwinCATStatePMPS motion.

    The LICMirror does not block beam while at a mirror state.
    This is because it has a hole in the middle of the mirror for the
    x-ray beam to travel through.

    This class also defines the state count as 4 (OUT and 3 targets)
    to limit the number of config PVs we connect to.
    """
    _transmission = {
        'MIRROR1': 1,
        'MIRROR2': 1,
    }
    config = UpCpt(state_count=4)


class LaserInCoupling(BaseInterface, GroupDevice, LightpathInOutCptMixin):
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
