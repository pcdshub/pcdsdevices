from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface, LightpathInOutMixin
from .pmps import TwinCATStatePMPS
from .sensors import TwinCATTempSensor


class ArrivalTimeMonitor(BaseInterface, Device, LightpathInOutMixin):
    tab_component_names = True

    lightpath_cpts = ['target']
    _icon = 'fa.clock-o'

    target = Cpt(TwinCATStatePMPS, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
    y_motor = Cpt(BeckhoffAxis, ':MMS:Y', kind='normal',
                  doc='Direct control of the diagnostic stack motor.')
    x_motor = Cpt(BeckhoffAxis, ':MMS:X', kind='normal',
                  doc='X position of target stack for alignment')

    thermocouple1 = Cpt(TwinCATTempSensor, ':STC:01', kind='normal',
                        doc='First thermocouple.')
