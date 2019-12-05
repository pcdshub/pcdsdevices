"""
Standard classes for LCLS Gauges
"""
import logging

from ophyd import EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV, Device
from ophyd import Component as Cpt, FormattedComponent as FCpt

from .doc_stubs import GaugeSet_base
from .interface import BaseInterface

logger = logging.getLogger(__name__)


class MKS937a(Device, BaseInterface):
    """
    Vacuum gauge controller MKS637a)

    A base class for an MKS637a controller

    Parameters
    ----------
    prefix : ``str``
        Full Gauge controller base PV

    name : ``str``
        Alias for the gauge controller
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


class BaseGauge(Device, BaseInterface):
    """
    Vacuum gauge

    A base class for a device with two limits switches controlled via an
    external command PV. This fully encompasses the controls `Stopper`
    installations as well as un-interlocked `GateValves`

    Parameters
    ----------
    prefix : ``str``
        Full Gauge base PV

    name : ``str``
        Alias for the gauge
    """
    pressure = Cpt(EpicsSignalRO, ':PMON', kind='hinted')
    egu = Cpt(EpicsSignalRO, ':PMON.EGU', kind='normal')
    state = Cpt(EpicsSignalRO, ':STATE', kind='normal')
    status = Cpt(EpicsSignalRO, ':STATUSMON', kind='normal')
    pressure_status = Cpt(EpicsSignalRO, ':PSTATMON', kind='normal')
    pressure_status_enable = Cpt(EpicsSignal, ':PSTATMSP', kind='normal')

    tab_component_names = True


class GaugePirani(BaseGauge):
    """
    Class for Pirani gauge
    """
    tab_component_names = True


class GaugeColdCathode(BaseGauge):
    """
    Class for Cold Cathode Gauge
    """
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


class GaugeSetBase(Device, BaseInterface):
    """
%s
    """
    __doc__ = __doc__ % GaugeSet_base
    gcc = FCpt(GaugeColdCathode, '{self.prefix}:GCC:{self.index}')
    tab_component_names = True

    def __init__(self, prefix, *, name, index, **kwargs):
        if isinstance(index, int):
            self.index = '%02d' % self.index
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

    prefix_controller : ``str``
        Base PV for the controller
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

    prefix_controller : ``str``
        Base PV for the controller
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
    Base class for gauges controlled by PLC

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
    state = Cpt(EpicsSignalRO, ':State_RBV', kind='hinted',
                doc='state of the gauge')


class GCCPLC(GaugePLC):
    """
    Class for Cold Cathode Gauge controlled by PLC

    """
    high_voltage_on = Cpt(EpicsSignalWithRBV, ':HV_SW', kind='normal',
                          doc='command to switch the hight voltage on')
    high_voltage_disable = Cpt(EpicsSignalRO, ':HV_DIS_RBV', kind='normal',
                               doc=('enables the high voltage on the cold '
                                    'cathode gauge'))
    protection_setpoint = Cpt(EpicsSignalRO, ':PRO_SP_RBV', kind='normal',
                              doc=('Protection setpoint for ion gauges at '
                                   'which the gauge turns off'))
    setpoint_hysterisis = Cpt(EpicsSignalWithRBV, ':SP_HYS', kind='config',
                              doc='Protection setpoint hysteresis')
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
                       doc='Interlock is ok')


class GCC500PLC(GCCPLC):
    """
    Class for GCC500 controlled by PLC

    """
    high_voltage_is_on = Cpt(EpicsSignalRO, ':HV_ON_RBV', kind='normal',
                             doc='state of the HV')
    disc_active = Cpt(EpicsSignalRO, ':DISC_ACTIVE_RBV', kind='normal',
                      doc='discharge current active')


class GCT(Device):
    """
    Base class for Gauge Controllers accessed via serial

    """
    unit = Cpt(EpicsSignal, ':UNIT', kind='omitted', doc='')
    cal = Cpt(EpicsSignal, ':CAL', kind='omitted', doc='')
    version = Cpt(EpicsSignalRO, ':VERSION', kind='omitted', doc='')


class MKS937BController(GCT):
    """
    Class for MKS937B accessed via serial

    """
    addr = Cpt(EpicsSignal, ':ADDR', kind='omitted', doc='')
    modtype_a = Cpt(EpicsSignalRO, ':MODTYPE_A', kind='omitted', doc='')
    modtype_b = Cpt(EpicsSignalRO, ':MODTYPE_B', kind='omitted', doc='')
    modtype_c = Cpt(EpicsSignalRO, ':MODTYPE_C', kind='omitted', doc='')
    pstatall = Cpt(EpicsSignalRO, ':PSTATALL', kind='omitted', doc='')
    pstatenall = Cpt(EpicsSignalRO, ':PSTATENALL', kind='omitted', doc='')
    slota = Cpt(EpicsSignal, ':SLOTA', kind='omitted', doc='')
    slotb = Cpt(EpicsSignal, ':SLOTB', kind='omitted', doc='')
    slotc = Cpt(EpicsSignal, ':SLOTC', kind='omitted', doc='')


class MKS937AController(GCT):
    """
    Class for MKS937A accessed via serial

    """
    pstatenout = Cpt(EpicsSignal, ':PSTATENOUT', kind='omitted', doc='')
    pstatspout = Cpt(EpicsSignal, ':PSTATSPOUT', kind='omitted', doc='')
    freq = Cpt(EpicsSignal, ':FREQ', kind='omitted', doc='')
    gauges = Cpt(EpicsSignalRO, ':GAUGES', kind='omitted', doc='')
    modcc = Cpt(EpicsSignalRO, ':MODCC', kind='omitted', doc='')
    moda = Cpt(EpicsSignalRO, ':MODA', kind='omitted', doc='')
    modb = Cpt(EpicsSignalRO, ':MODB', kind='omitted', doc='')
    com_des = Cpt(EpicsSignal, ':COM_DES', kind='omitted', doc='')
    com = Cpt(EpicsSignal, ':COM', kind='omitted', doc='')
    delay = Cpt(EpicsSignal, ':DELAY', kind='omitted', doc='')
    front = Cpt(EpicsSignal, ':FRONT', kind='omitted', doc='')


class GaugeSerial(Device):
    """
    Base class for Vacuum Gauge controlled via serial

    """
    gastype = Cpt(EpicsSignal, ':GASTYPE', kind='omitted', doc='')
    gastypedes = Cpt(EpicsSignal, ':GASTYPEDES', kind='omitted', doc='')
    hystsprbck_1 = Cpt(EpicsSignalRO, ':HYSTSPRBCK_1', kind='omitted', doc='')
    hystsprbck_2 = Cpt(EpicsSignalRO, ':HYSTSPRBCK_2', kind='omitted', doc='')
    p = Cpt(EpicsSignal, ':P', kind='omitted', doc='')
    padel = Cpt(EpicsSignal, ':PADEL', kind='omitted', doc='')
    plog = Cpt(EpicsSignal, ':PLOG', kind='omitted', doc='')
    pmon = Cpt(EpicsSignal, ':PMON', kind='omitted', doc='')
    pmonraw = Cpt(EpicsSignal, ':PMONRAW', kind='omitted', doc='')
    pstat_1 = Cpt(EpicsSignal, ':PSTAT_1', kind='omitted', doc='')
    pstat_2 = Cpt(EpicsSignal, ':PSTAT_2', kind='omitted', doc='')
    pstat_calc = Cpt(EpicsSignal, ':PSTAT_CALC', kind='omitted', doc='')
    pstat_sum = Cpt(EpicsSignal, ':PSTAT_SUM', kind='omitted', doc='')
    pstatdirdes_1 = Cpt(EpicsSignal, ':PSTATDIRDES_1', kind='omitted', doc='')
    pstatdirdes_2 = Cpt(EpicsSignal, ':PSTATDIRDES_2', kind='omitted', doc='')
    pstatenable_1 = Cpt(EpicsSignal, ':PSTATENABLE_1', kind='omitted', doc='')
    pstatenable_2 = Cpt(EpicsSignal, ':PSTATENABLE_2', kind='omitted', doc='')
    pstatenades_1 = Cpt(EpicsSignal, ':PSTATENADES_1', kind='omitted', doc='')
    pstatenades_2 = Cpt(EpicsSignal, ':PSTATENADES_2', kind='omitted', doc='')
    pstatspdes_1 = Cpt(EpicsSignal, ':PSTATSPDES_1', kind='omitted', doc='')
    pstatspdes_2 = Cpt(EpicsSignal, ':PSTATSPDES_2', kind='omitted', doc='')
    pstatspdir_1 = Cpt(EpicsSignal, ':PSTATSPDIR_1', kind='omitted', doc='')
    pstatspdir_2 = Cpt(EpicsSignal, ':PSTATSPDIR_2', kind='omitted', doc='')
    pstatsprbck_1 = Cpt(EpicsSignalRO, ':PSTATSPRBCK_1', kind='omitted',
                        doc='')
    pstatsprbck_2 = Cpt(EpicsSignalRO, ':PSTATSPRBCK_2', kind='omitted',
                        doc='')
    state = Cpt(EpicsSignal, ':STATE', kind='omitted', doc='')
    statedes = Cpt(EpicsSignal, ':STATEDES', kind='omitted', doc='')
    staterbck = Cpt(EpicsSignalRO, ':STATERBCK', kind='omitted', doc='')
    status_rs = Cpt(EpicsSignal, ':STATUS_RS', kind='omitted', doc='')
    status_rs_calc1 = Cpt(EpicsSignal, ':STATUS_RS_CALC1', kind='omitted',
                          doc='')
    status_rs_calc2 = Cpt(EpicsSignal, ':STATUS_RS_CALC2', kind='omitted',
                          doc='')
    status_rscalc = Cpt(EpicsSignal, ':STATUS_RSCALC', kind='omitted',
                        doc='')
    status_rscalc2 = Cpt(EpicsSignal, ':STATUS_RSCALC2', kind='omitted',
                         doc='')
    status_rsmon = Cpt(EpicsSignal, ':STATUS_RSMON', kind='omitted', doc='')
    status_rsout = Cpt(EpicsSignal, ':STATUS_RSOUT', kind='omitted', doc='')


class GaugeSerialGPI(GaugeSerial):
    """
    Class for Pirani Vacuum Gauge controlled via serial

    """
    atmcalib = Cpt(EpicsSignal, ':ATMCALIB', kind='omitted', doc='')
    atmcalibdes = Cpt(EpicsSignal, ':ATMCALIBDES', kind='omitted', doc='')
    autozero = Cpt(EpicsSignal, ':AUTOZERO', kind='omitted', doc='')
    autozerodes = Cpt(EpicsSignal, ':AUTOZERODES', kind='omitted', doc='')
    zeropr = Cpt(EpicsSignal, ':ZEROPR', kind='omitted', doc='')


class GaugeSerialGCC(GaugeSerial):
    """
    Class for Cold Cathode Gauge controlled via serial

    """
    pctrl_ch_des = Cpt(EpicsSignal, ':PCTRL_CH_DES', kind='omitted', doc='')
    pctrl_ch_rbck = Cpt(EpicsSignalRO, ':PCTRL_CH_RBCK', kind='omitted',
                        doc='')
    pctrldes = Cpt(EpicsSignal, ':PCTRLDES', kind='omitted', doc='')
    pctrlen = Cpt(EpicsSignal, ':PCTRLEN', kind='omitted', doc='')
    pctrlencalc = Cpt(EpicsSignal, ':PCTRLENCALC', kind='omitted', doc='')
    pctrlenrbck = Cpt(EpicsSignalRO, ':PCTRLENRBCK', kind='omitted', doc='')
    pctrlrbck = Cpt(EpicsSignalRO, ':PCTRLRBCK', kind='omitted', doc='')
    pctrlspdes = Cpt(EpicsSignal, ':PCTRLSPDES', kind='omitted', doc='')
    pctrlsprbck = Cpt(EpicsSignalRO, ':PCTRLSPRBCK', kind='omitted', doc='')
    pprotencalc = Cpt(EpicsSignal, ':PPROTENCALC', kind='omitted', doc='')
    pprotenrbck = Cpt(EpicsSignalRO, ':PPROTENRBCK', kind='omitted', doc='')
    pprotspdes = Cpt(EpicsSignal, ':PPROTSPDES', kind='omitted', doc='')
    pprotsprbck = Cpt(EpicsSignalRO, ':PPROTSPRBCK', kind='omitted', doc='')
    pstat_3 = Cpt(EpicsSignal, ':PSTAT_3', kind='omitted', doc='')
    pstat_4 = Cpt(EpicsSignal, ':PSTAT_4', kind='omitted', doc='')
    pstatdirdes_3 = Cpt(EpicsSignal, ':PSTATDIRDES_3', kind='omitted', doc='')
    pstatdirdes_4 = Cpt(EpicsSignal, ':PSTATDIRDES_4', kind='omitted', doc='')
    pstatenable_3 = Cpt(EpicsSignal, ':PSTATENABLE_3', kind='omitted', doc='')
    pstatenable_4 = Cpt(EpicsSignal, ':PSTATENABLE_4', kind='omitted', doc='')
    pstatenades_3 = Cpt(EpicsSignal, ':PSTATENADES_3', kind='omitted', doc='')
    pstatenades_4 = Cpt(EpicsSignal, ':PSTATENADES_4', kind='omitted', doc='')
    pstatspdes_3 = Cpt(EpicsSignal, ':PSTATSPDES_3', kind='omitted', doc='')
    pstatspdes_4 = Cpt(EpicsSignal, ':PSTATSPDES_4', kind='omitted', doc='')
    pstatspdes_fs = Cpt(EpicsSignal, ':PSTATSPDES_FS', kind='omitted', doc='')
    pstatspdir_3 = Cpt(EpicsSignal, ':PSTATSPDIR_3', kind='omitted', doc='')
    pstatspdir_4 = Cpt(EpicsSignal, ':PSTATSPDIR_4', kind='omitted', doc='')
    pstatsprbck_3 = Cpt(EpicsSignal, ':PSTATSPRBCK_3', kind='omitted', doc='')
    pstatsprbck_4 = Cpt(EpicsSignal, ':PSTATSPRBCK_4', kind='omitted', doc='')
    pstatsprbck_fs = Cpt(EpicsSignal, ':PSTATSPRBCK_FS', kind='omitted',
                         doc='')


# factory function for IonPumps
def GaugeSet(prefix, *, name, index, **kwargs):
    """
    Factory function for Gauge Set

    Parameters
    ----------
    prefix : ``str``
        Gauge base PV (up to GCC/GPI)

    name : ``str``
        Alias for the gauge set

    index : ``str`` or ``int``
        Index for gauge (e.g. '02' or 3)

    (optional) prefix_controller : ``str``
        Base PV for the controller

    (optional) onlyGCC:
        if defined and not false, set has no Pirani
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
