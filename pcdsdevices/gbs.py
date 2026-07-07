import numpy as np
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

    rtd1 = Cpt(TwinCATTempSensor, ':RTD:01', kind='normal', doc='First RTD.')
    rtd2 = Cpt(TwinCATTempSensor, ':RTD:02', kind='normal', doc='Second RTD.')

    def get_current_grating_period(self):
        """
        Get the grating period based on current grating target position.

        Returns
        -------
        str
            current target grating
        """

        return self.get_grating_period(self.target.position)

    def get_grating_period(self, target_pos):
        """
        Get the grating period associated with a given target position based on hardcoded
        table provided by Haoyuan.

        Returns
        str
            current target grating period

        Raises
        ------
        ValueError
            If input target is invalid
        """

        # map between targets and motor position values
        target_map = {}

        for state in self.target.config.component_names:
            state_obj = getattr(self.target.config, state)
            target_name = state_obj.state_name.get()
            setpoint = state_obj.setpoint.get()
            target_map[target_name] = np.abs(setpoint)

        # check if target exists
        if target_pos not in target_map.keys():
            raise ValueError(f"{target_pos} not in list, possible targets are: {list(target_map.keys())}")

        grating_y_position = target_map[target_pos]

        # grating period 650nm motor positions
        positions_650 = np.array([33.105, 44.776, 56.120])

        # grating period 980nm motor positions
        positions_980 = np.array([31.605, 43.264, 54.618])

        if np.any(np.abs(grating_y_position - positions_980) <= 1):
            grating_period = 980e-6  # mm

        elif np.any(np.abs(grating_y_position - positions_650) <= 1):
            grating_period = 650e-6  # mm

        else:
            # Set a grating period for the no-grating case.
            grating_period = None

        return grating_period
