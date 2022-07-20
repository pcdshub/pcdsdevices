from ophyd import Component as Cpt

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis, EpicsMotorInterface
from .interface import BaseInterface, LightpathInOutCptMixin
from .pmps import TwinCATStatePMPS
from .signal import PytmcSignal


class ReflaserL2SIMirror(TwinCATStatePMPS):
    """
    Controls the reference laser's states.

    Defines the state count as 2 (OUT and IN) to limit the number of
    config PVs we connect to.
    """
    config = UpCpt(state_count=2)


class ReflaserL2SI(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    """
    The L2SI design for the reference laser.

    The reference laser is an optical laser that is pointed down the beam
    path in lieu of the x-ray beam. This is useful for alignment purposes
    and to verify a through path from the reference laser to the sample
    chamber.
    """
    tab_component_names = True

    lightpath_cpts = ['mirror']
    _icon = 'fa.bullseye'

    las_pct = Cpt(PytmcSignal, ':LAS:PCT', io='io', kind='hinted')
    mirror = Cpt(ReflaserL2SIMirror, ':MMS:STATE', kind='hinted',
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
