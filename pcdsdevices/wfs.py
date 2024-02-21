from ophyd import Component as Cpt

from .analog_signals import FDQ
from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .digital_signals import J120K
from .epics_motor import BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathInOutCptMixin
from .pmps import TwinCATStatePMPS
from .sensors import TwinCATTempSensor


class WaveFrontSensorStates(TwinCATStatePMPS):
    """
    Controls the WFS (Wavefront Sensor)'s target states.

    Defines the state count as 6 (OUT and 5 targets) to limit the number of
    config PVs we connect to.
    """
    config = UpCpt(state_count=6)


class WaveFrontSensorTarget(BaseInterface, GroupDevice,
                            LightpathInOutCptMixin):
    """
    An array of targets used to determine the beam's wavefront.

    Each target is a waveplate that results in a characteristic pattern
    on a downstream imager (PPM or XTES Imager) that can be used to determine
    information about the wavefront.

    """
    tab_component_names = True

    lightpath_cpts = ['target']
    _icon = 'fa.ellipsis-v'

    target = Cpt(WaveFrontSensorStates, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
    y_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:Y', kind='normal',
                  doc='Direct control of the diagnostic stack motor.')
    z_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:Z', kind='normal',
                  doc='Z position of target stack for focus control.')

    thermocouple1 = Cpt(TwinCATTempSensor, ':STC:01', kind='normal',
                        doc='First thermocouple.')
    thermocouple2 = Cpt(TwinCATTempSensor, ':STC:02', kind='normal',
                        doc='Second thermocouple.')


class WaveFrontSensorTargetFDQ(WaveFrontSensorTarget):
    """
    An array of targets used to determine the beam's wavefront.

    With a Kenyence FDQ flow meter installed.
    """
    flow_meter = Cpt(FDQ, '', kind='normal',
                     doc='Device that measures PCW Flow Rate.')


class WaveFrontSensorTargetCool(WaveFrontSensorTarget):
    """
    An array of targets used to determine the beam's wavefront.

    This array has a cooling indication switch.
    """
    flow_switch = Cpt(J120K, '', kind='normal',
                      doc='Device that indicates nominal PCW Flow Rate.')
