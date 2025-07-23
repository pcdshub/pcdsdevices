from ophyd import Component as Cpt

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxisNoOffset
from .interface import BaseInterface, LightpathInOutCptMixin
from .pmps import TwinCATStatePMPS
from .sensors import TwinCATTempSensor


class GratingBeamSplitterStates(TwinCATStatePMPS):
    """
    Controls the GBS (Grating Beam Splitter)'s target states.

    Defines the state count as 7 (OUT and 6 targets) to limit the number of
    config PVs we connect to.
    """
    config = UpCpt(state_count=7)


class GratingBeamSplitterTarget(BaseInterface, GroupDevice,
                                LightpathInOutCptMixin):
    """
    An array of targets used to determine the beam's wavefront. Similar to
    the WFS with a unique substrate.

    Each target is a waveplate that results in a characteristic pattern
    on a downstream imager (PPM or XTES Imager) that can be used to determine
    information about the wavefront.
    """
    tab_component_names = True

    lightpath_cpts = ['target']
    _icon = 'fa.ellipsis-v'

    target = Cpt(GratingBeamSplitterStates, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
    y_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:Y', kind='normal',
                  doc='Direct control of the diagnostic stack motor.')

    thermocouple1 = Cpt(TwinCATTempSensor, ':STC:01', kind='normal',
                        doc='First thermocouple.')
    thermocouple2 = Cpt(TwinCATTempSensor, ':STC:02', kind='normal',
                        doc='Second thermocouple.')
