"""
Standard classes for LCLS Gauges.
"""
import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd import FormattedComponent as FCpt

from .doc_stubs import GaugeSet_base
from .interface import BaseInterface

logger = logging.getLogger(__name__)


class MKS937a(BaseInterface, Device):
    """
    A base class for an MKS637a vacuum gauge controller.

    Parameters
    ----------
    prefix : str
        Full Gauge controller base PV.

    name : str
        A name to refer to the gauge controller.
    """

    frequence = Cpt(EpicsSignal, ':FREQ', kind='normal')
    unit = Cpt(EpicsSignal, ':UNIT', kind='normal')
    version = Cpt(EpicsSignalRO, ':VERSION', kind='config')
    cc_delay = Cpt(EpicsSignalRO, ':DELAY', kind='config')
    A1_A2_slot = Cpt(EpicsSignalRO, ':MODA', kind='config')
    B1_B2_slot = Cpt(EpicsSignalRO, ':MODB', kind='config')
    user_calibration = Cpt(EpicsSignalRO, ':CAL', kind='config')
    frontpanel = Cpt(EpicsSignalRO, ':FRONT', kind='config')

    command = Cpt(EpicsSignal, ':COM', write_pv=':COM_DES', kind='config')

    tab_component_names = True


class BaseGauge(BaseInterface, Device):
    """
    Base class for vacuum gauges.

    A base class for a device with two limits switches controlled via an
    external command PV. This fully encompasses the controls :class:`Stopper`
    installations as well as un-interlocked :class:`GateValves`.

    Parameters
    ----------
    prefix : str
        Full gauge base PV.

    name : str
        A name to refer to the gauge.
    """

    pressure = Cpt(EpicsSignalRO, ':PMON', kind='hinted')
    egu = Cpt(EpicsSignalRO, ':PMON.EGU', kind='normal')
    state = Cpt(EpicsSignalRO, ':STATE', kind='normal')
    status = Cpt(EpicsSignalRO, ':STATUSMON', kind='normal')
    pressure_status = Cpt(EpicsSignalRO, ':PSTATMON', kind='normal')
    pressure_status_enable = Cpt(EpicsSignal, ':PSTATMSP', kind='normal')

    tab_component_names = True


class GaugePirani(BaseGauge):
    """Class for Pirani gauges."""
    tab_component_names = True


class GaugeColdCathode(BaseGauge):
    """Class for Cold Cathode Gauges."""
    enable = Cpt(EpicsSignal, ':ENBL_SW', kind='normal')
    relay_setpoint = Cpt(EpicsSignal, ':PSTATSPRBCK',
                         write_pv=':PSTATSPDES', kind='normal')
    relay_enable = Cpt(EpicsSignal, ':PSTATENRBCK',
                       write_pv=':PSTATEN', kind='normal')
    control_setpoint = Cpt(EpicsSignal, ':PCTRLSPRBCK',
                           write_pv=':PCTRLSPDES', kind='normal')
    control_enable = Cpt(EpicsSignal, ':PCTRLENRBCK',
                         write_pv=':PCTRLEN', kind='normal')
    protection_setpoint = Cpt(EpicsSignal, ':PPROTSPRBCK',
                              write_pv=':PPROTSPDES', kind='normal')
    protection_enable = Cpt(EpicsSignal, ':PPROTENRBCK',
                            write_pv=':PPROTEN', kind='normal')

    tab_component_names = True


class GaugeSetBase(BaseInterface, Device):
    """
%s
    """
    __doc__ = __doc__ % GaugeSet_base

    gcc = FCpt(GaugeColdCathode, '{self.prefix}:GCC:{self.index}')
    tab_component_names = True

    def __init__(self, prefix, *, name, index, **kwargs):
        if isinstance(index, int):
            self.index = '%02d' % index
        else:
            self.index = index
        super().__init__(prefix, name=name, **kwargs)

    def pressure(self):
        if self.gcc.state.get() == 0:
            return self.gcc.pressure.get()
        else:
            return -1.

    def egu(self):
        return self.gcc.egu.get()


class GaugeSetMks(GaugeSetBase):
    """
%s

    prefix_controller : str
        Base PV for the controller.
    """
    __doc__ = (__doc__ % GaugeSet_base).replace(
        'Set', 'Set w/o Pirani, but with controller')

    controller = FCpt(MKS937a, '{self.prefix_controller}')
    tab_component_names = True

    def __init__(self, prefix, *, name, index, prefix_controller, **kwargs):
        self.prefix_controller = prefix_controller
        super().__init__(prefix, name=name, index=index, **kwargs)

    def egu(self):
        return self.controller.unit.get()


class GaugeSetPirani(GaugeSetBase):
    """
%s
    """
    __doc__ = __doc__ % GaugeSet_base

    gpi = FCpt(GaugePirani, '{self.prefix}:GPI:{self.index}')
    tab_component_names = True

    def pressure(self):
        if self.gcc.state.get() == 0:
            return self.gcc.pressure.get()
        else:
            return self.gpi.pressure.get()


class GaugeSetPiraniMks(GaugeSetPirani):
    """
%s

    prefix_controller : str
        Base PV for the controller.
    """
    __doc__ = (__doc__ % GaugeSet_base).replace(
        'Set', 'Set including the controller')

    controller = FCpt(MKS937a, '{self.prefix_controller}')
    tab_component_names = True

    def __init__(self, prefix, *, name, index, prefix_controller, **kwargs):
        self.prefix_controller = prefix_controller
        super().__init__(prefix, name=name, index=index, **kwargs)

    def egu(self):
        return self.controller.unit.get()


class GaugePLC(Device):
    """
    Base class for gauges controlled by PLC.

    Newer class. This and below are still missing some functionality.
    Still need to work out replacement of old classes.
    """

    pressure = Cpt(EpicsSignalRO, ':PRESS_RBV', kind='hinted',
                   doc='gauge pressure reading')
    gauge_at_vac = Cpt(EpicsSignalRO, ':AT_VAC_RBV', kind='normal',
                       doc='gauge is at VAC')
    pressure_ok = Cpt(EpicsSignalRO, ':PRESS_OK_RBV', kind='normal',
                      doc='pressure reading ok')
    at_vac_setpoint = Cpt(EpicsSignalWithRBV, ':VAC_SP', kind='config',
                          doc='At vacuum setpoint for all gauges')
    state = Cpt(EpicsSignalRO, ':STATE_RBV', kind='hinted',
                doc='state of the gauge')


class GCCPLC(GaugePLC):
    """Class for a Cold Cathode Gauge controlled by PLC."""
    high_voltage_on = Cpt(EpicsSignalWithRBV, ':HV_SW', kind='normal',
                          doc='command to switch the high voltage on')
    high_voltage_disable = Cpt(EpicsSignalRO, ':HV_DIS_DO_RBV', kind='normal',
                               doc=('enables the high voltage on the cold '
                                    'cathode gauge'))
    protection_setpoint = Cpt(EpicsSignalWithRBV, ':PRO_SP', kind='normal',
                              doc=('Protection setpoint for ion gauges at '
                                   'which the gauge turns off'))
    setpoint_hysterisis = Cpt(EpicsSignalWithRBV, ':SP_HYS', kind='config',
                              doc='Protection setpoint hysteresis')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
                       doc='Interlock is ok')


class GHCPLC(GaugePLC):
    """Class for a Hot Cathode Gauge controlled by PLC."""
    high_voltage_on = Cpt(EpicsSignalWithRBV, ':HV_SW', kind='normal',
                          doc='command to switch the high voltage on')
    high_voltage_disable = Cpt(EpicsSignalRO, ':HV_DIS_DO_RBV', kind='normal',
                               doc=('enables the high voltage on the hot '
                                    'cathode gauge'))
    protection_setpoint = Cpt(EpicsSignalWithRBV, ':PRO_SP', kind='normal',
                              doc=('Protection setpoint for ion gauges at '
                                   'which the gauge turns off'))
    setpoint_hysterisis = Cpt(EpicsSignalWithRBV, ':SP_HYS', kind='config',
                              doc='Protection setpoint hysteresis')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
                       doc='Interlock is ok')


class GCC500PLC(GCCPLC):
    """Class for a GCC500 controlled by PLC."""
    high_voltage_is_on = Cpt(EpicsSignalRO, ':HV_ON_RBV', kind='normal',
                             doc='state of the HV')
    disc_active = Cpt(EpicsSignalRO, ':DISC_ACTIVE_RBV', kind='normal',
                      doc='discharge current active')


class GCT(Device):
    """Base class for Gauge Controllers accessed via serial."""
    unit = Cpt(EpicsSignal, ':UNIT', kind='omitted')
    cal = Cpt(EpicsSignal, ':CAL', kind='omitted')
    version = Cpt(EpicsSignalRO, ':VERSION_RBV', kind='omitted')


class MKS937BController(GCT):
    """Class for MKS937B gauge controllers accessed via serial."""
    addr = Cpt(EpicsSignal, ':ADDR', kind='omitted')
    modtype_a = Cpt(EpicsSignalRO, ':MODTYPE_A_RBV', kind='omitted')
    modtype_b = Cpt(EpicsSignalRO, ':MODTYPE_B_RBV', kind='omitted')
    modtype_c = Cpt(EpicsSignalRO, ':MODTYPE_C_RBV', kind='omitted')
    pstatall = Cpt(EpicsSignalRO, ':PSTATALL_RBV', kind='omitted')
    pstatenall = Cpt(EpicsSignalRO, ':PSTATENALL_RBV', kind='omitted')
    slota = Cpt(EpicsSignal, ':SLOTA', kind='omitted')
    slotb = Cpt(EpicsSignal, ':SLOTB', kind='omitted')
    slotc = Cpt(EpicsSignal, ':SLOTC', kind='omitted')


class MKS937AController(GCT):
    """Class for MKS937A gauge controllers accessed via serial."""
    pstatenout = Cpt(EpicsSignal, ':PSTATENOUT', kind='omitted')
    pstatspout = Cpt(EpicsSignal, ':PSTATSPOUT', kind='omitted')
    freq = Cpt(EpicsSignal, ':FREQ', kind='omitted')
    gauges = Cpt(EpicsSignalRO, ':GAUGES_RBV', kind='omitted')
    modcc = Cpt(EpicsSignalRO, ':MODCC_RBV', kind='omitted')
    moda = Cpt(EpicsSignalRO, ':MODA_RBV', kind='omitted')
    modb = Cpt(EpicsSignalRO, ':MODB_RBV', kind='omitted')
    com_des = Cpt(EpicsSignal, ':COM_DES', kind='omitted')
    com = Cpt(EpicsSignal, ':COM', kind='omitted')
    delay = Cpt(EpicsSignal, ':DELAY', kind='omitted')
    front = Cpt(EpicsSignal, ':FRONT', kind='omitted')


class GaugeSerial(Device):
    """Base class for Vacuum Gauges controlled via serial."""
    gastype = Cpt(EpicsSignal, ':GASTYPE', kind='omitted')
    gastypedes = Cpt(EpicsSignal, ':GASTYPEDES', kind='omitted')
    hystsprbck_1 = Cpt(EpicsSignalRO, ':HYSTSPRBCK_1_RBV', kind='omitted')
    hystsprbck_2 = Cpt(EpicsSignalRO, ':HYSTSPRBCK_2_RBV', kind='omitted')
    p = Cpt(EpicsSignal, ':P', kind='omitted')
    padel = Cpt(EpicsSignal, ':PADEL', kind='omitted')
    plog = Cpt(EpicsSignal, ':PLOG', kind='omitted')
    pmon = Cpt(EpicsSignal, ':PMON', kind='omitted')
    pmonraw = Cpt(EpicsSignal, ':PMONRAW', kind='omitted')
    pstat_1 = Cpt(EpicsSignal, ':PSTAT_1', kind='omitted')
    pstat_2 = Cpt(EpicsSignal, ':PSTAT_2', kind='omitted')
    pstat_calc = Cpt(EpicsSignal, ':PSTAT_CALC', kind='omitted')
    pstat_sum = Cpt(EpicsSignal, ':PSTAT_SUM', kind='omitted')
    pstatdirdes_1 = Cpt(EpicsSignal, ':PSTATDIRDES_1', kind='omitted')
    pstatdirdes_2 = Cpt(EpicsSignal, ':PSTATDIRDES_2', kind='omitted')
    pstatenable_1 = Cpt(EpicsSignal, ':PSTATENABLE_1', kind='omitted')
    pstatenable_2 = Cpt(EpicsSignal, ':PSTATENABLE_2', kind='omitted')
    pstatenades_1 = Cpt(EpicsSignal, ':PSTATENADES_1', kind='omitted')
    pstatenades_2 = Cpt(EpicsSignal, ':PSTATENADES_2', kind='omitted')
    pstatspdes_1 = Cpt(EpicsSignal, ':PSTATSPDES_1', kind='omitted')
    pstatspdes_2 = Cpt(EpicsSignal, ':PSTATSPDES_2', kind='omitted')
    pstatspdir_1 = Cpt(EpicsSignal, ':PSTATSPDIR_1', kind='omitted')
    pstatspdir_2 = Cpt(EpicsSignal, ':PSTATSPDIR_2', kind='omitted')
    pstatsprbck_1 = Cpt(EpicsSignalRO, ':PSTATSPRBCK_1_RBV', kind='omitted')
    pstatsprbck_2 = Cpt(EpicsSignalRO, ':PSTATSPRBCK_2_RBV', kind='omitted')
    state = Cpt(EpicsSignal, ':STATE', kind='omitted')
    statedes = Cpt(EpicsSignal, ':STATEDES', kind='omitted')
    staterbck = Cpt(EpicsSignalRO, ':STATERBCK_RBV', kind='omitted')
    status_rs = Cpt(EpicsSignal, ':STATUS_RS', kind='omitted')
    status_rs_calc1 = Cpt(EpicsSignal, ':STATUS_RS_CALC1', kind='omitted')
    status_rs_calc2 = Cpt(EpicsSignal, ':STATUS_RS_CALC2', kind='omitted')
    status_rscalc = Cpt(EpicsSignal, ':STATUS_RSCALC', kind='omitted')
    status_rscalc2 = Cpt(EpicsSignal, ':STATUS_RSCALC2', kind='omitted')
    status_rsmon = Cpt(EpicsSignal, ':STATUS_RSMON', kind='omitted')
    status_rsout = Cpt(EpicsSignal, ':STATUS_RSOUT', kind='omitted')


class GaugeSerialGPI(GaugeSerial):
    """Class for Pirani Vacuum Gauges controlled via serial."""
    atmcalib = Cpt(EpicsSignal, ':ATMCALIB', kind='omitted')
    atmcalibdes = Cpt(EpicsSignal, ':ATMCALIBDES', kind='omitted')
    autozero = Cpt(EpicsSignalRO, ':AUTOZERO_RBV', kind='omitted')
    autozerodes = Cpt(EpicsSignal, ':AUTOZERODES', kind='omitted')
    zeropr = Cpt(EpicsSignal, ':ZEROPR', kind='omitted')


class GaugeSerialGCC(GaugeSerial):
    """Class for Cold Cathode Gauges controlled via serial."""
    pctrl_ch_des = Cpt(EpicsSignal, ':PCTRL_CH_DES', kind='omitted')
    pctrl_ch_rbck = Cpt(EpicsSignalRO, ':PCTRL_CH_RBCK_RBV', kind='omitted')
    pctrldes = Cpt(EpicsSignal, ':PCTRLDES', kind='omitted')
    pctrlen = Cpt(EpicsSignal, ':PCTRLEN', kind='omitted')
    pctrlencalc = Cpt(EpicsSignal, ':PCTRLENCALC', kind='omitted')
    pctrlenrbck = Cpt(EpicsSignalRO, ':PCTRLENRBCK_RBV', kind='omitted')
    pctrlrbck = Cpt(EpicsSignalRO, ':PCTRLRBCK_RBV', kind='omitted')
    pctrlspdes = Cpt(EpicsSignal, ':PCTRLSPDES', kind='omitted')
    pctrlsprbck = Cpt(EpicsSignalRO, ':PCTRLSPRBCK_RBV', kind='omitted')
    pprotencalc = Cpt(EpicsSignal, ':PPROTENCALC', kind='omitted')
    pprotenrbck = Cpt(EpicsSignalRO, ':PPROTENRBCK_RBV', kind='omitted')
    pprotspdes = Cpt(EpicsSignal, ':PPROTSPDES', kind='omitted')
    pprotsprbck = Cpt(EpicsSignalRO, ':PPROTSPRBCK_RBV', kind='omitted')
    pstat_3 = Cpt(EpicsSignal, ':PSTAT_3', kind='omitted')
    pstat_4 = Cpt(EpicsSignal, ':PSTAT_4', kind='omitted')
    pstatdirdes_3 = Cpt(EpicsSignal, ':PSTATDIRDES_3', kind='omitted')
    pstatdirdes_4 = Cpt(EpicsSignal, ':PSTATDIRDES_4', kind='omitted')
    pstatenable_3 = Cpt(EpicsSignal, ':PSTATENABLE_3', kind='omitted')
    pstatenable_4 = Cpt(EpicsSignal, ':PSTATENABLE_4', kind='omitted')
    pstatenades_3 = Cpt(EpicsSignal, ':PSTATENADES_3', kind='omitted')
    pstatenades_4 = Cpt(EpicsSignal, ':PSTATENADES_4', kind='omitted')
    pstatspdes_3 = Cpt(EpicsSignal, ':PSTATSPDES_3', kind='omitted')
    pstatspdes_4 = Cpt(EpicsSignal, ':PSTATSPDES_4', kind='omitted')
    pstatspdes_fs = Cpt(EpicsSignal, ':PSTATSPDES_FS', kind='omitted')
    pstatspdir_3 = Cpt(EpicsSignal, ':PSTATSPDIR_3', kind='omitted')
    pstatspdir_4 = Cpt(EpicsSignal, ':PSTATSPDIR_4', kind='omitted')
    pstatsprbck_3 = Cpt(EpicsSignal, ':PSTATSPRBCK_3', kind='omitted')
    pstatsprbck_4 = Cpt(EpicsSignal, ':PSTATSPRBCK_4', kind='omitted')
    pstatsprbck_fs = Cpt(EpicsSignal, ':PSTATSPRBCK_FS', kind='omitted')


# factory function for IonPumps
def GaugeSet(prefix, *, name, index, **kwargs):
    """
    Factory function for Gauge Set.

    Parameters
    ----------
    prefix : str
        Gauge base PV (up to 'GCC'/'GPI').

    name : str
        Name to refer to the gauge set.

    index : str or int
        Index for gauge (e.g. '02' or 3).

    prefix_controller : str, optional
        Base PV for the controller.

    onlyGCC : optional
        If defined and not :keyword:`False`, set has no Pirani.
    """

    onlyGCC = kwargs.pop('onlyGCC', None)
    if onlyGCC:
        if 'prefix_controller' in kwargs:
            return GaugeSetMks(
                prefix, name=name, index=index,
                prefix_controller=kwargs.pop('prefix_controller'),
                **kwargs)
        else:
            return GaugeSetBase(prefix, name=name, index=index, **kwargs)
    else:
        if 'prefix_controller' in kwargs:
            return GaugeSetPiraniMks(
                prefix, name=name, index=index,
                prefix_controller=kwargs.pop('prefix_controller'),
                **kwargs)
        else:
            return GaugeSetPirani(prefix, name=name, index=index, **kwargs)
