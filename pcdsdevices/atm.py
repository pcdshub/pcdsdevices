from ophyd import Component as Cpt

from .analog_signals import FDQ
from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis, BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathInOutCptMixin
from .pmps import TwinCATStatePMPS
from .sensors import TwinCATTempSensor


class ATMTarget(TwinCATStatePMPS):
    """
    Controls the ATM (ArrivalTimeMonitor)'s states.

    Defines the state count as 6 (OUT and 5 targets) to limit the number of
    config PVs we connect to.
    """
    config = UpCpt(state_count=6)


class ArrivalTimeMonitor(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    """
    Determines the arrival time of the x-ray relative to the optical laser.

    This Python class controls the motors and reads back the thermocouple,
    but does not contain the timing data.

    This device is also known as the ATM.
    """
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
    flow_meter = Cpt(FDQ, '', kind='normal',
                     doc='Device that measures PCW Flow Rate.')


class TM1K4Target(ATMTarget):
    """
    Controls TM1K4's states, and ATM in TMO.

    Defines the state count as 9 (OUT and 8 targets), three more than the
    standard ATM.
    """
    config = UpCpt(state_count=9)


class TM1K4(ArrivalTimeMonitor):
    """
    An ATM in TMO that has two extra target states.
    """

    target = Cpt(TM1K4Target, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')


class TM2K4Target(ATMTarget):
    """
    Controls TM2K4's states, an ATM in TMO.

    Defines the state count as 9 (OUT and 8 targets), three more than the
    standard ATM.
    """
    config = UpCpt(state_count=9)


class TM2K4(ArrivalTimeMonitor):
    """
    An ATM in TMO that has one fewer target state.
    """

    target = Cpt(TM2K4Target, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
    flow_meter = None


class TM2K2Target(ATMTarget):
    """
    Controls TM2K2's states, an ATM in RIX.

    Defines the state count as 7 (OUT and 6 targets), one more than the
    standard ATM.
    """
    config = UpCpt(state_count=7)


class TM2K2(ArrivalTimeMonitor):
    """
    An ATM in RIX that has one extra target state.
    """
    target = Cpt(TM2K2Target, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')


class MFXATM(ArrivalTimeMonitor):
    """
    An ATM in MFX that has no cooling.
    """
    flow_meter = None
