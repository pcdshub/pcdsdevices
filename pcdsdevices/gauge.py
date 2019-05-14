"""
Standard classes for LCLS Gauges
"""
import logging
from ophyd import EpicsSignal, EpicsSignalRO, Device
from ophyd import Component as Cpt, FormattedComponent as FCpt
from .doc_stubs import GaugeSet_base

logger = logging.getLogger(__name__)


class MKS937a(Device):
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


class BaseGauge(Device):
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


class GaugePirani(BaseGauge):
    """
    Class for Pirani gauge
    """
    pass


class GaugeColdCathode(BaseGauge):
    """
    Class for Cold Cathode Gauge
    """
    enable = Cpt(EpicsSignal, ':ENBL_SW', kind='normal')
    relaySetpoint = Cpt(EpicsSignal, ':PSTATSPRBCK',
                        write_pv=':PSTATSPDES', kind='normal')
    relayEnable = Cpt(EpicsSignal, ':PSTATENRBCK',
                      write_pv=':PSTATEN', kind='normal')
    controlSetpoint = Cpt(EpicsSignal, ':PCTRLSPRBCK',
                          write_pv=':PCTRLSPDES', kind='normal')
    controlEnable = Cpt(EpicsSignal, ':PCTRLENRBCK',
                        write_pv=':PCTRLEN', kind='normal')
    protectionSetpoint = Cpt(EpicsSignal, ':PPROTSPRBCK',
                             write_pv=':PPROTSPDES', kind='normal')
    protectionEnable = Cpt(EpicsSignal, ':PPROTENRBCK',
                           write_pv=':PPROTEN', kind='normal')


class GaugeSetBase(Device):
    """
%s
    """
    __doc__ = __doc__ % GaugeSet_base
    gcc = FCpt(GaugeColdCathode, '{self.prefix}:GCC:{self.index}')

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

    def __init__(self, prefix, *, name, index, prefix_controller,  **kwargs):
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

    def __init__(self, prefix, *, name, index, prefix_controller,  **kwargs):
        self.prefix_controller = prefix_controller
        super().__init__(prefix, name=name, index=index, **kwargs)

    def egu(self):
        return self.controller.unit.get()


# factory function for IonPumps
def GaugeSet(prefix, *, name, index, **kwargs):

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
