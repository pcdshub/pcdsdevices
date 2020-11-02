"""
Module for the L2SI Laser MODS Table TILEs and Table classes.
"""
from ophyd import Device
from ophyd import Component as Cpt

from pcdsdevices.epics_motor import SmarAct, SmarActTipTilt
from pcdsdevices.areadetector.detectors import LasBasler

from pcdsdevices.lasers.tuttifrutti import TuttiFrutti, TuttiFruttiCls
from pcdsdevices.lasers.zoomtelescope import ZoomTelescope
from pcdsdevices.lasers.ek9000 import EnvironmentalMonitor, El3174AiCh
from pcdsdevices.lasers.elliptec import EllLinear, EllRotation, Ell9


### Generic TILE Devices
class TileBase(Device):
    """
    Base class for MODS TILEs.
    """
    pass


class InjectionTile(TileBase):
    """
    Class for L2SI MODS injection TILE. Common to several installations.

    Parameters
    ----------
    prefix : str
        Five character prefix for particular MODS installation, e.g. LM1K4
        (TMO).

    name : str
        Name for the device, e.g. tmo_mods_inj_tile

    Examples
    --------
    # TMO Injection TILE
    tmo_inj = InjectionTile('LM1K4', 'tmo_inj')
    # ChemRIXS Injection TILE
    crixs_inj = InjectionTile('LM2K2', 'crixs_inj')
    """
    zoom_telescope = Cpt(ZoomTelescope, ':INJ_MP1_ZOO1', kind='normal')
    waveplate1 = Cpt(SmarAct, ':INJ_MP1_ATT1_WP1', kind='normal')
    waveplate2 = Cpt(SmarAct, ':INJ_MP1_ATT1_WP2', kind='normal')
    mp1_mr1 = Cpt(SmarActTipTilt, ':INJ_MP1_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    dp2_mr1 = Cpt(SmarAct, ':INJ_DP2_MR1')
    dp1_tf1 = Cpt(TuttiFruttiCls('', 'inj_dp1_tf1', nf=True, ff=True, ell=True),
                  ':INJ_DP1_TF1', kind='normal')
    dp2_tf1 = Cpt(TuttiFruttiCls('', 'inj_dp2_tf1', spec=True, pm=True, ell=True,
                                 wfs=True),
                  ':INJ_DP2_TF1', kind='normal')
    env_sensors = Cpt(EnvironmentalMonitor, '_BHC_AI_01', kind='normal')


class CompressorTile(TileBase):
    """
    Class for L2SI MODS compressor TILE. Common to several installations.

    Parameters
    ----------
    prefix : str
        Five character prefix for particular MODS installation, e.g. LM1K4
        (TMO).

    name : str
        Name for the device, e.g. tmo_mods_com_tile

    Examples
    --------
    # TMO Compressor TILE
    tmo_com = CompressorTile('LM1K4', 'tmo_com')
    # ChemRIXS Compressor TILE
    crixs_com = CompressorTile('LM2K2', 'crixs_com')
    """
    mp1_mr1 = Cpt(SmarActTipTilt, ':COM_MP1_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp1_mr4 = Cpt(SmarActTipTilt, ':COM_MP1_MR4', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp1_gt2_lm1 = Cpt(SmarAct, ':COM_MP1_GT2_LM1', kind='normal')
    mp1_mr8 = Cpt(SmarActTipTilt, ':COM_MP1_MR8', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp2_dly1 = Cpt(SmarAct, ':COM_MP2_DLY1', kind='normal')
    mp2_bs2 = Cpt(SmarActTipTilt, ':COM_MP2_BS2', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    dp1_mr1 = Cpt(SmarAct, ':COM_DP1_MR1', kind='normal')
    dp1_tf1 = Cpt(TuttiFruttiCls('', 'com_dp1_tf1', nf=True, ff=True,
                  ell=True),
                  ':COM_DP1_TF1', kind='normal')
    dp2_xtl1 = Cpt(EllLinear, ':COM_DP2_XTL1:ELL', port=0, channel=1,
                   kind='normal')
    dp2_tf1 = Cpt(TuttiFruttiCls('', 'com_dp2_tf1', nf=True, ff=True, ell=True,
                                 spec=True, pm=True),
                                 ':COM_DP2_TF1', kind='normal')
    dp3_tf1 = Cpt(TuttiFruttiCls('', 'com_dp3_tf1', nf=True, ff=True, ell=True,
                                 pm=True),
                                 ':COM_DP3_TF1', kind='normal')
    env_sensors = Cpt(EnvironmentalMonitor, '_BHC_AI_01', kind='normal')


class HarmonicsTile(TileBase):
    """
    Class for L2SI MODS harmonics TILE. Common to several installations.

    Parameters
    ----------
    prefix : str
        Five character prefix for particular MODS installation, e.g. LM1K4
        (TMO).

    name : str
        Name for the device, e.g. tmo_mods_hrm_tile

    Examples
    --------
    # TMO Harmonics TILE
    tmo_hrm = HarmonicsTile('LM1K4', 'tmo_hrm')
    # ChemRIXS Compressor TILE
    crixs_hrm = HarmonicsTile('LM2K2', 'crixs_hrm')
    """
    mp1_mr1 = Cpt(SmarActTipTilt, ':HRM_MP1_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp1_mr1_lm1 = Cpt(SmarAct, ':HRM_MP1_MR1_LM1', kind='normal')
    mp1_mr4 = Cpt(SmarActTipTilt, ':HRM_MP4_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp1_spo1 = Cpt(SmarAct, ':HRM_MP1_SPO1', kind='normal')
    mp1_mr7 = Cpt(SmarActTipTilt, ':HRM_MP7_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp1_pc1 = Cpt(SmarAct, ':HRM_MP1_PC1', kind='normal')
    mp1_pc1_pzm2 = Cpt(SmarAct, ':HRM_MP1_PC1', kind='normal')
    mp1_mr8 = Cpt(SmarActTipTilt, ':HRM_MP8_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp1_mr8_lm1 = Cpt(SmarAct, ':HRM_MP1_MR8_LM1', kind='normal')
    mp3_mr1 = Cpt(SmarActTipTilt, ':HRM_MP3_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp3_mr1_lm1 = Cpt(SmarAct, ':HRM_MP3_MR1_LM1', kind='normal')
    mp3_mr2 = Cpt(SmarActTipTilt, ':HRM_MP2_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp3_mr2_lm1 = Cpt(SmarAct, ':HRM_MP3_MR2_LM1', kind='normal')
    dp1_tf1 = Cpt(TuttiFruttiCls('', 'hrm_dp1_tf1', nf=True, ff=True,
                  ell=True, pm=True),
                  ':HRM_DP1_TF1', kind='normal')
    dp1_tf2 = Cpt(TuttiFruttiCls('', 'hrm_dp2_tf1', nf=True, ff=True,
                  ell=True, pm=True, spec=True),
                  ':HRM_DP1_TF1', kind='normal')


### Hutch-specific TILE Devices
class XppInjectionTile(TileBase):
    """
    Class for the XPP injection TILE.

    Parameters
    ----------
    prefix : str
        Five character prefix for particular MODS installation, e.g. LMXPP.

    name : str
        Name for the device, e.g. xpp_inj_tile

    Examples
    --------
    # XPP Injection TILE
    xpp_inj = XppInjectionTile('LMXPP', 'xpp_inj')
    """
    mp1_mr1 = Cpt(SmarActTipTilt, ':INJ_MP1_MR1', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    zoom_telescope = Cpt(ZoomTelescope, ':INJ_MP1_ZOO1', kind='normal')
    mp1_mr4 = Cpt(SmarActTipTilt, ':INJ_MP1_MR4', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    mp1_mr5 = Cpt(SmarActTipTilt, ':INJ_MP1_MR5', tip_pv='_TIP1',
                  tilt_pv='_TILT1', kind='normal')
    dp1_tf1 = Cpt(TuttiFruttiCls('', 'inj_dp1_tf1', nf=True, ff=True, ell=True),
                  ':INJ_DP1_TF1', kind='normal')
    dp2_tf1 = Cpt(TuttiFruttiCls('', 'inj_dp2_tf1', spec=True, pm=True, ell=True,
                                 wfs=True),
                  ':INJ_DP2_TF1', kind='normal')
    env_sensors = Cpt(EnvironmentalMonitor, '_BHC_AI_01', kind='normal')


class TmoEjectionTile(TileBase):
    """
    Class for the TMO Ejection TILE.

    Parameters
    ----------
    prefix : str
        Five character prefix for particular MODS installation, e.g. LM1k4.

    name : str
        Name for the device, e.g. tmo_ejx_tile

    Examples
    --------
    # TMO Ejection TILE
    tmo_ejx = TmoEjectionTile('LM1K4', 'tmo_ejx')
    """
    mp1_mr1 = Cpt(SmarActTipTilt, ':EJX_MP1_MR1', tip_pv='_TIP1',
                 tilt_pv='_TILT1', kind='normal')
    mp1_mr2 = Cpt(SmarActTipTilt, ':EJX_MP1_MR2', tip_pv='_TIP1',
                 tilt_pv='_TILT1', kind='normal')
    mp1_s41 = Cpt(Ell9, ':EJX_MP1_S41', port=0, channel=1, kind='normal')
    mp1_s42 = Cpt(Ell9, ':EJX_MP2_S41', port=0, channel=2, kind='normal')
    mp1_mr3 = Cpt(SmarAct, ':EJX_MP1_MR3', kind='normal')
    mp1_oap1 = Cpt(SmarAct, ':EJX_MP1_OAP1', kind='normal')
    mp1_oap1_mr1 = Cpt(SmarActTipTilt, ':EJX_OAP1', tip_pv='_TIP1',
                       tilt_pv='_TILT1', kind='normal')
    mp1_oap1_mr3 = Cpt(SmarActTipTilt, ':EJX_OAP1', tip_pv='_TIP3',
                       tilt_pv='_TILT3', kind='normal')
    #TODO    


class TmoAtmTile(TileBase):
    """
    Class for L2SI TMO MODS ATM TILE. Unique to TMO.

    Parameters
    ----------
    prefix : str
        Five character prefix for particular MODS installation, e.g. LM1K4
        (TMO).

    name : str
        Name for the device, e.g. tmo_mods_atm_tile

    Examples
    --------
    # TMO ATM TILE
    tmo_atm = TmoAtmTile('LM1K4', 'tmo_atm')
    """
    mp1_mr1 = Cpt(SmarActTipTilt, ':ATM_MP1_MR1', tip_pv='_TIP1',
                 tilt_pv='_TILT1', kind='normal')
    mp1_mr3 = Cpt(SmarActTipTilt, ':ATM_MP1_MR3', tip_pv='_TIP1',
                 tilt_pv='_TILT1', kind='normal')
    mp1_wp1_rm1 = Cpt(EllRotation, ':ATM_MP1_WP1_RM1:ELL', port=0, channel=3,
                      kind='normal')
    mp1_wp1_lm1 = Cpt(EllLinear, ':ATM_MP1_WP1_LM1:ELL', port=0, channel=2,
                      kind='normal')
    mp2_pol1 = Cpt(EllRotation, ':ATM_MP2_POL1:ELL', port=0, channel=1,
                   kind='normal')
    # TODO: Add diode once it's ready
    dp1_tf1 = Cpt(TuttiFruttiCls('', 'atm_dp1_tf1', nf=True, ff=True,
                  ell=True),
                  ':ATM_DP1_TF1', kind='normal')
    # TODO: Add diode once it's ready
    dp2_tf1 = Cpt(TuttiFruttiCls('', 'atm_dp2_tf1', nf=True, ff=True,
                  ell=True, pm=True, spec=True),
                  ':ATM_DP2_TF1', kind='normal')


class ChemRixsAtmTile(TileBase):
    """
    Class for L2SI ChemRIXS MODS ATM TILE. Unique to ChemRIXS.

    Parameters
    ----------
    prefix : str
        Five character prefix for particular MODS installation, e.g. LM2K2
        (ChemRIXS).

    name : str
        Name for the device, e.g. crixs_mods_atm_tile

    Examples
    --------
    # ChemRIXS ATM TILE
    crixs_atm = ChemRixsAtmTile('LM1K4', 'crixs_atm')
    """
    mp1_mr3 = Cpt(SmarActTipTilt, ':ATM_MP1_MR3', tip_pv='_TIP1',
                 tilt_pv='_TILT1', kind='normal')
    mp1_mr6 = Cpt(SmarActTipTilt, ':ATM_MP1_MR6', tip_pv='_TIP1',
                 tilt_pv='_TILT1', kind='normal')
    mp1_wp1_rm1 = Cpt(EllRotation, ':ATM_MP1_WP1_RM1:ELL', port=0, channel=3,
                      kind='normal')
    mp1_wp1_lm1 = Cpt(EllLinear, ':ATM_MP1_WP1_LM1:ELL', port=0, channel=2,
                      kind='normal')
    mp2_pol1 = Cpt(EllRotation, ':ATM_MP2_POL1:ELL', port=0, channel=1,
                   kind='normal')
    # TODO: Add diode once it's ready
    dp1_tf1 = Cpt(TuttiFruttiCls('', 'atm_dp1_tf1', nf=True, ff=True,
                  ell=True, pm=True, spec=True),
                  ':ATM_DP1_TF1', kind='normal')
