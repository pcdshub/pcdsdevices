from ophyd import Component as Cpt

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis, BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathInOutMixin
from .pmps import TwinCATStatePMPS
from .sensors import TwinCATTempSensor


class ATMTarget(TwinCATStatePMPS):
    config = UpCpt(state_count=6)


class ArrivalTimeMonitor(BaseInterface, GroupDevice, LightpathInOutMixin):
    tab_component_names = True

    lightpath_cpts = ['target']
    _icon = 'fa.clock-o'

    target = Cpt(ATMTarget, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
    y_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:Y', kind='normal',
                  doc='Direct control of the diagnostic stack motor.')
    x_motor = Cpt(BeckhoffAxis, ':MMS:X', kind='normal',
                  doc='X position of target stack for alignment')

    thermocouple1 = Cpt(TwinCATTempSensor, ':STC:01', kind='normal',
                        doc='First thermocouple.')


class TM2K2Target(ATMTarget):
    config = UpCpt(state_count=7)


class TM2K2(ArrivalTimeMonitor):
    target = Cpt(TM2K2Target, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
