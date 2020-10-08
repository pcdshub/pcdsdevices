from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface, LightpathInOutMixin
from .pmps import TwinCATStatePMPS


class LaserInCoupling(BaseInterface, Device, LightpathInOutMixin):
    tab_component_names = True

    lightpath_cpts = ['mirror']
    _icon = 'fa.dot-circle-o'

    mirror = Cpt(TwinCATStatePMPS, ':MMS:STATE', kind='hinted',
                 doc='Control of the mirror via saved positions.')
    y_motor = Cpt(BeckhoffAxis, ':MMS', kind='normal',
                  doc='Direct control of the mirror motor.')
