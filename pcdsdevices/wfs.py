from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .inout import TwinCATInOutPositioner
from .interface import BaseInterface, LightpathInOutMixin
from .sensors import TwinCATTempSensor


class WaveFrontSensorTarget(BaseInterface, Device, LightpathInOutMixin):
    tab_component_names = True

    lightpath_cpts = ['target']
    _icon = 'fa.ellipsis-v'

    target = Cpt(TwinCATInOutPositioner, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
    y_motor = Cpt(BeckhoffAxis, ':MMS:Y', kind='normal',
                  doc='Direct control of the diagnostic stack motor.')
    z_motor = Cpt(BeckhoffAxis, ':MMS:Z', kind='normal',
                  doc='Z position of target stack for focus control.')

    thermocouple1 = Cpt(TwinCATTempSensor, ':STC:01', kind='normal',
                        doc='First thermocouple.')
    thermocouple2 = Cpt(TwinCATTempSensor, ':STC:02', kind='normal',
                        doc='Second thermocouple.')
