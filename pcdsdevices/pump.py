"""
Standard classes for LCLS Gauges
"""
import logging
from ophyd import EpicsSignal, EpicsSignalRO, Device
from ophyd import Component as Cpt, FormattedComponent as FCpt
from .doc_stubs import IonPump_base
from .interface import BaseInterface

logger = logging.getLogger(__name__)


class TurboPump(Device, BaseInterface):
    """
    Vacuum Pump
    """
    atspeed = Cpt(EpicsSignal, ':ATSPEED_DI', kind='normal')
    start = Cpt(EpicsSignal, ':START_SW', kind='normal')

    tab_whitelist = ['run', 'stop', 'atspeed']

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)


class EbaraPump(Device, BaseInterface):
    """
    Ebara Turbo Pump
    """
    start = Cpt(EpicsSignal, ':MPSTART_SW', kind='normal')

    tab_whitelist = ['run', 'stop']

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)


class GammaController(Device, BaseInterface):
    """
    Ion Pump Gamma controller
    """
    channel1name = Cpt(EpicsSignal, ':CHAN1NAME', kind='config')
    channel2name = Cpt(EpicsSignal, ':CHAN2NAME', kind='config')
    model = Cpt(EpicsSignalRO, ':MODEL', kind='config')
    firmwareversion = Cpt(EpicsSignalRO, ':FWVERSION', kind='config')
    linevoltage = Cpt(EpicsSignalRO, ':LINEV', kind='omitted')
    linefrequency = Cpt(EpicsSignalRO, ':LINEFREQ', kind='omitted')
    cooling_fan_status = Cpt(EpicsSignalRO, ':FAN', kind='omitted')

    power_autosave = Cpt(EpicsSignal, ':ASPOWERE', write_pv=':ASPOWEREDES',
                         kind='config')
    high_voltage_enable_autosave = Cpt(EpicsSignal, ':ASHVE',
                                       write_pv=':ASHVEDES', kind='normal')

    unit = Cpt(EpicsSignal, ':PEGUDES', kind='normal')

    tab_component_names = True


class IonPumpBase(Device, BaseInterface):
    """
%s
    """
    __doc__ = (__doc__ % IonPump_base).replace('Ion Pump',
                                               'Ion Pump Base Class')

    _pressure = Cpt(EpicsSignalRO, ':PMON', kind='hinted')
    _egu = Cpt(EpicsSignalRO, ':PMON.EGU', kind='omitted')
    current = Cpt(EpicsSignalRO, ':IMON', kind='normal')
    voltage = Cpt(EpicsSignalRO, ':VMON', kind='normal')
    status_code = Cpt(EpicsSignalRO, ':STATUSCODE', kind='normal', string=True)
    status = Cpt(EpicsSignalRO, ':STATUS', kind='normal')
    # check if this work as its an enum
    state = Cpt(EpicsSignal, ':STATEMON', write_pv=':STATEDES', kind='normal',
                string=True)
    # state_cmd = Cpt(EpicsSignal, ':STATEDES', kind='normal')

    pumpsize = Cpt(EpicsSignal, ':PUMPSIZEDES', write_pv=':PUMPSIZE',
                   kind='omitted')
    controllername = Cpt(EpicsSignal, ':VPCNAME', kind='omitted')
    hvstrapping = Cpt(EpicsSignal, ':VDESRBCK', kind='omitted')
    supplysize = Cpt(EpicsSignalRO, ':SUPPLYSIZE', kind='omitted')

    aomode = Cpt(EpicsSignal, ':AOMODEDES', write_pv=':AOMODE', kind='config')
    calfactor = Cpt(EpicsSignal, ':CALFACTORDES', write_pv=':CALFACTOR',
                    kind='config')

    tab_whitelist = ['on', 'off', 'info', 'pressure']
    tab_component_names = True

    def on(self):
        self.state.put(1)

    def off(self):
        self.state.put(0)

    def info(self):
        outString = (
            '%s is an ion pump  with base PV %s which is %s \n' %
            (self.name, self.prefix, self.state.get()))
        if self.state.get() == 'ON':
            outString += 'Pressure: %g \n' % self.pressure()
            outString += 'Current: %g \n' % self.current.get()
            outString += 'Voltage: %g' % self.voltage.get()
        return outString

    def pressure(self):
        if self.state.get() == 'ON':
            return self._pressure.get()
        else:
            return -1.

    def egu(self):
        return self._egu.get()


class IonPumpWithController(IonPumpBase):
    """
%s

    prefix_controller : ``str``
        Ion Pump Controller base PV

    """
    __doc__ = (__doc__ % IonPump_base).replace('Pump', 'Pump w/ controller')

    controller = FCpt(GammaController, '{self.prefix_controller}')

    tab_component_names = True

    def __init__(self, prefix, *, prefix_controller, **kwargs):
        # base PV for ion pump controller
        self.prefix_controller = prefix_controller
        # Load Ion Pump itself
        super().__init__(prefix, **kwargs)

    def egu(self):
        return self.controller.unit.get()


# factory function for IonPumps
def IonPump(prefix, *, name, **kwargs):
    """
    Ion Pump

    Parameters
    ----------
    prefix : ``str``
        Ion Pump PV

    name : ``str``
        Alias for the ion pump

    (optional) prefix_controller : ``str``
        Ion Pump Controller base PV
    """

    if 'prefix_controller' not in kwargs:
        return IonPumpBase(prefix, name=name, **kwargs)

    return IonPumpWithController(prefix, name=name,  **kwargs)
