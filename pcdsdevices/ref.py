from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis, EpicsMotorInterface
from .interface import BaseInterface, LightpathInOutMixin
from .pmps import TwinCATStatePMPS
from .signal import PytmcSignal


class ReflaserL2SI(BaseInterface, Device, LightpathInOutMixin):
    tab_component_names = True

    lightpath_cpts = ['mirror']
    _icon = 'fa.bullseye'

    las_pct = Cpt(PytmcSignal, ':LAS:PCT', io='io', kind='hinted')
    mirror = Cpt(TwinCATStatePMPS, ':MMS:STATE', kind='hinted',
                 doc='In/Out control of Reflaser Mirror')
    y_motor = Cpt(BeckhoffAxis, ':MMS', kind='normal',
                  doc='Direct control of mirror motor.')
    pico1 = Cpt(EpicsMotorInterface, ':MCP:01', kind='config',
                doc='Laser alignment 01')
    pico2 = Cpt(EpicsMotorInterface, ':MCP:02', kind='config',
                doc='Laser alignment 02')
    pico3 = Cpt(EpicsMotorInterface, ':MCP:03', kind='config',
                doc='Laser alignment 03')
    pico4 = Cpt(EpicsMotorInterface, ':MCP:04', kind='config',
                doc='Laser alignment 04')
