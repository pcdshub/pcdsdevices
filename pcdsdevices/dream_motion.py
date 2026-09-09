"""
DREAM Motion Classes
This module contains classes related to the TMO-DREAM Motion System

"""

from ophyd import Component as Cpt
from ophyd import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis, SmarAct, SmarActEtherCAT
from .interface import BaseInterface
from .pmps import TwinCATStatePMPS
from .signal import PytmcSignal
from .slits import MetaDataDict
from .state import StatePositioner
from .utils import reorder_components
from .variety import set_metadata


class TMODream(BaseInterface, GroupDevice):
    """
    Dream Motion Class

    This class controls motors fixed to the dream in-air Motion system for the Dream
    endstation in TMO with the Gas Nozzle, Gas jet, Coil and Main Chamber Y.

    Parameters
    ----------
    prefix : str
        Base PV for the DREAM motion system
        DREAM:
    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    gas_nozzle_x = Cpt(BeckhoffAxis, ":GSJN:MMS:X", doc="dream gas nozzle x axis", kind="normal")
    gas_nozzle_y = Cpt(BeckhoffAxis, ":GSJN:MMS:Y", doc="dream gas nozzle y axis", kind="normal")
    gas_nozzle_z = Cpt(BeckhoffAxis, ":GSJN:MMS:Z", doc="dream gas nozzle z axis", kind="normal")
    gas_jet_x = Cpt(BeckhoffAxis, ":GSJP:MMS:X", doc="dream gas jet x axis", kind="normal")
    gas_jet_z = Cpt(BeckhoffAxis, ":GSJP:MMS:Z", doc="dream gas jet z axis", kind="normal")
    coil_roll = Cpt(BeckhoffAxis, ":COIL:MMS:ROLL", doc="dream coil roll axis", kind="normal")
    coil_yaw = Cpt(BeckhoffAxis, ":COIL:MMS:YAW", doc="dream coil yaw axis", kind="normal")
    chamber_y = Cpt(BeckhoffAxis, ":MC:MMS:Y", doc="dream main chamber Y axis", kind="normal")


class DREAM_SL3K4(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls DREAM SL3K4 SmarAct based scatter slit

    Parameters
    ----------
    prefix : str
        DREAM:
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    top = Cpt(SmarActEtherCAT, ':MMT:Y1', kind='normal')
    bottom = Cpt(SmarActEtherCAT, ':MMT:Y2', kind='normal')
    north = Cpt(SmarActEtherCAT, ':MMT:X1', kind='normal')
    south = Cpt(SmarActEtherCAT, ':MMT:X2', kind='normal')
    top_bypass = Cpt(PytmcSignal, ':bEpsY1Bypass', io='io', kind='hinted', doc='EPS Bypass')
    bottom_bypass = Cpt(PytmcSignal, ':bEpsY2Bypass', io='io', kind='hinted', doc='EPS Bypass')
    north_bypass = Cpt(PytmcSignal, ':bEpsX1Bypass', io='io', kind='hinted', doc='EPS Bypass')
    south_bypass = Cpt(PytmcSignal, ':bEpsX2Bypass', io='io', kind='hinted', doc='EPS Bypass')

    drift_tol = Cpt(PytmcSignal, ':fDriftTol', io='io', kind='hinted', doc='Blades drifting tolerance')
    blades_drift = Cpt(PytmcSignal, ':aBladesfDrift', io='i', kind='hinted', doc='Array of blade drifts in  order [X1, X2, Y1, Y2]')
    blades_drifted = Cpt(PytmcSignal, ':aBladesfDrifted', io='i', kind='hinted', doc='Blades drift status in  order [X1, X2, Y1, Y2]')
    drift_status = Cpt(PytmcSignal, ':bDrift', io='i', kind='hinted', doc='SL3K4 drift status')

    reset = Cpt(PytmcSignal, ':RESET', io='io', kind='hinted', doc='Global reset')
    status_msg = Cpt(PytmcSignal, ':sStatusMsg', io='i', kind='hinted', doc='Status message')
    state_set = Cpt(PytmcSignal, ':STATE:SET', io='io', kind='hinted', doc='SL3K4 state setter')
    state_get = Cpt(PytmcSignal, ':STATE:GET', io='i', kind='hinted', doc='SL3K4 state getter')
    arb_enable = Cpt(PytmcSignal, ':STATE:PMPS:ARB:ENABLE', io='io', kind='config',
                     doc='Enables PMPS pre-emptive protections. This can be '
                         'disabled to fall back on fast-fault-only '
                         'protections. Disabling this will also clear '
                         'arbiter requests.')
    maint_mode = Cpt(PytmcSignal, ':STATE:PMPS:MAINT', io='io', kind='config',
                     doc='If this is on, we trip a fast fault and then can '
                         'move the motor freely. Useful for debugging '
                         'motion issues.')
    ref_refresh = Cpt(PytmcSignal, ':REFRENCING:REFRESH', io='io', kind='hinted',
                      doc='Must-reference re-home interval in seconds')
    must_home = Cpt(PytmcSignal, ':MUSTHOME:ACTIVE', io='i', kind='hinted',
                    doc='Re-home mandatory, move blocked')
    all_homed = Cpt(PytmcSignal, ':ALLHOMED', io='i', kind='hinted',
                    doc='TRUE when all blades report homed')

    def __init__(self, prefix, cam, data_source, *, name, **kwargs):
        self._cam = cam
        self._data_source = data_source
        super().__init__(prefix, name=name, **kwargs)
        self.md = MetaDataDict({"cam": cam,
                                "data_source": data_source,
                                "input_branches": None,
                                "output_branches": None})


class DREAM_Sample_Paddle_SmarAct_State(StatePositioner):
    state = Cpt(
        EpicsSignal,
        "_RBV",
        write_pv="",
        kind="hinted",
        doc="Setpoint and readback for state position.",
    )


class DREAM_Sample_Paddle_SmarAct_Axis_State(TwinCATStatePMPS):
    config = UpCpt(state_count=10)


@reorder_components(
    start_with=['state', 'maint_mode']
)
class DREAM_Sample_Paddle(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls sample paddle X,Y, Z, and Ret motors fixed to the DREAM Motion system for the
    DREAM endstation in TMO.
    Parameters
    ----------
    prefix : str
        DREAM:
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True
    # Motor components
    state = Cpt(DREAM_Sample_Paddle_SmarAct_State, ':STATE', kind='hinted', doc='Sample paddle state')
    set_metadata(state, dict(variety='command-enum'))
    maint_mode = Cpt(PytmcSignal, ':MAINTMODE', io='io', kind='hinted', doc='DGPD sequence mover maintenance mode')
    x = Cpt(SmarActEtherCAT, ':MMT:X', kind='normal')
    y = Cpt(SmarActEtherCAT, ':MMT:Y', kind='normal')
    z = Cpt(SmarActEtherCAT, ':MMT:Z', kind='normal')
    ret = Cpt(SmarActEtherCAT, ':MMT:RET', kind='normal')
    x_state = Cpt(DREAM_Sample_Paddle_SmarAct_Axis_State, ':X:STATE', kind='hinted', doc='X state mover')
    y_state = Cpt(DREAM_Sample_Paddle_SmarAct_Axis_State, ':Y:STATE', kind='hinted', doc='Y state mover')
    z_state = Cpt(DREAM_Sample_Paddle_SmarAct_Axis_State, ':Z:STATE', kind='hinted', doc='Z state mover')
    ret_state = Cpt(DREAM_Sample_Paddle_SmarAct_Axis_State, ':RET:STATE', kind='hinted', doc='Ret state mover')
    seq_state = Cpt(PytmcSignal, ':SEQSTATE', io='i', kind='hinted', doc='Sequence mover state', string=True)
    seq_enable = Cpt(PytmcSignal, ':SEQENABLE', io='io', kind='hinted', doc='DGPD sequence mover enable/disable')
    reset = Cpt(PytmcSignal, ':RESET', io='io', kind='hinted', doc='DGPD sequence mover reset')
    ret_eps_bypass = Cpt(PytmcSignal, ':bEpsRETBypass', io='io', kind='hinted', doc='RET EPS Bypass')
    x_eps_bypass = Cpt(PytmcSignal, ':bEpsXBypass', io='io', kind='hinted', doc='X EPS Bypass')
    y_eps_bypass = Cpt(PytmcSignal, ':bEpsYBypass', io='io', kind='hinted', doc='Y EPS Bypass')
    z_eps_bypass = Cpt(PytmcSignal, ':bEpsZBypass', io='io', kind='hinted', doc='Z EPS Bypass')
    safety_loop_status = FCpt(PytmcSignal, 'DREAM:SL:STATUS', io='i', kind='hinted', doc='DREAM Safety Loop Status')
    safety_loop_enable = FCpt(PytmcSignal, 'DREAM:SL:ENABLE', io='io', kind='hinted', doc='DREAM Safety Loop Enable')


class DREAM_Gas_Jet_Slits(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls gas jet slits north, south, east, and west motors fixed to the DREAM Motion system for the
    DREAM endstation in TMO.
    Parameters
    ----------
    prefix : str
        TMO:DREAM:MCS2:01
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True
    # Motor components
    north = Cpt(SmarAct, ':m5', kind='normal')
    south = Cpt(SmarAct, ':m10', kind='normal')
    east = Cpt(SmarAct, ':m6', kind='normal')
    west = Cpt(SmarAct, ':m11', kind='normal')
