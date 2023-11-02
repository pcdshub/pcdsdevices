"""
Standard classes for LCLS Energy Monitors.
"""
import logging

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO, SignalRO

from .interface import BaseInterface
from .keithley import K6514

logger = logging.getLogger(__name__)


class GEM(BaseInterface, Device):
    """
    Gas Energy Monitor from the LUSI project.

    A base class for a Gas Energy Monitor.

    Parameters
    ----------
    prefix : str
        Full GEM base PV.

    name : str
        Name to refer to the GEM.
    """

    not_implemented = Cpt(SignalRO, name="Not Implemented",
                          value="Not Implemented", kind='normal')


class GMDPreAmp(BaseInterface, Device):
    tab_component_names = True
    ion_pre_att = Cpt(EpicsSignal, ':AMP_PREATTN1_RBV', write_pv=':AMP_PREATTN1', string=True, kind='normal', doc='Channel 1 PRE attenuator')
    ion_post_att = Cpt(EpicsSignal, ':AMP_POSATTN1_RBV', write_pv=':AMP_POSATTN1', string=True, kind='normal', doc='Channel 1 POS attenuator')
    elec1_pre_att = Cpt(EpicsSignal, ':AMP_PREATTN2_RBV', write_pv=':AMP_PREATTN2', string=True, kind='normal', doc='Channel 2 PRE attenuator')
    elec1_post_att = Cpt(EpicsSignal, ':AMP_POSATTN2_RBV', write_pv=':AMP_POSATTN2', string=True, kind='normal', doc='Channel 2 POS attenuator')
    elec2_pre_att = Cpt(EpicsSignal, ':AMP_PREATTN3_RBV', write_pv=':AMP_PREATTN3', string=True, kind='normal', doc='Channel 3 PRE attenuator')
    elec2_post_att = Cpt(EpicsSignal, ':AMP_POSATTN3_RBV', write_pv=':AMP_POSATTN3', string=True, kind='normal', doc='Channel 3 POS attenuator')
    spare_pre_att = Cpt(EpicsSignal, ':AMP_PREATTN4_RBV', write_pv=':AMP_PREATTN4', string=True, kind='normal', doc='Channel 4 PRE attenuator')
    spare_post_att = Cpt(EpicsSignal, ':AMP_POSATTN4_RBV', write_pv=':AMP_POSATTN4', string=True, kind='normal', doc='Channel 4 POS attenuator')


class GMD(BaseInterface, Device):
    """
    Gas Monitor Detector, installed in the LCLS-II XTES project.

    A base class for a GMD.

    Parameters
    ----------
    prefix : str
        Full GMD base PV.

    name : str
        Name to refer to the GMD.
    """
    tab_component_names = True
    avg_int = Cpt(EpicsSignalRO, ':HPS:AvgPulseIntensity', kind='hinted',
                  doc='Avg Pulse energy [mJ]')
    mj = Cpt(EpicsSignalRO, ':HPS:milliJoulesPerPulse', kind='hinted',
             doc='Pulse energy [mJ]')
    photons = Cpt(EpicsSignalRO, ':HPS:AvgPhotonsPerPulse', kind='hinted',
                  doc='photons')
    transmission = Cpt(EpicsSignalRO, ':HPS:AvgTransmission', kind='hinted',
                       doc='transmission')
    gas_type = Cpt(EpicsSignalRO, ':GAS_TYPE_RBV', string=True, kind='hinted',
                   doc='Gas Type')
    mean_charge = Cpt(EpicsSignal, ':HPS:MeanCharge', write_pv=':HPS:MeanCharge:Manual', kind='normal',
                      doc='Mean Charge used in energy calculation')
    xsection = Cpt(EpicsSignal, ':HPS:CrossSection', write_pv=':HPS:CrossSection:Manual', kind='normal',
                   doc='Photoionization cross section used in energy calculation')
    keithley_sum = Cpt(EpicsSignalRO, ':HPS:KeithleySum', kind='normal',
                       doc='')
    pressure = Cpt(EpicsSignalRO, ':GSR:1:Calib:Pressure:Calc', kind='normal',
                   doc='Gas pressure in energy monitor')
    mean_charge_source = Cpt(EpicsSignal, ':HPS:MeanCharge:Source', string=True, kind='omitted',
                             doc='Source value of mean charge (Gas Table or Manual) for energy calculation')
    xsection_source = Cpt(EpicsSignal, ':HPS:MeanCharge:Source', string=True, kind='omitted',
                          doc='Source value of photoionization cross section (Gas Table or Manual) for energy calculation')
    temperature = Cpt(EpicsSignalRO, ':RTD:1:TEMP_RBV', kind='hinted', doc='')
    beam_position_x = Cpt(EpicsSignalRO, ':HPS:PosXSLOW', kind='hinted',
                          doc='beam position x in GMD')
    beam_position_y = Cpt(EpicsSignalRO, ':HPS:PosYSLOW', kind='hinted',
                          doc='beam position y in GMD')
    preamp = Cpt(GMDPreAmp, ':HPS', kind='omitted')
    keithley1 = Cpt(K6514, ':ETM:01', kind='omitted')
    keithley2 = Cpt(K6514, ':ETM:02', kind='omitted')


class XGMD(BaseInterface, Device):
    """
    X Gas Monitor Detector (2nd generation GMD).

    A base class for an XGMD, installed in the LCLS-II XTES project.

    Parameters
    ----------
    prefix : str
        Full XGMD base PV.

    name : str
        Name to refer to the XGMD.
    """

    not_implemented = Cpt(SignalRO, name="Not Implemented",
                          value="Not Implemented", kind='normal')
