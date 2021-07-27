import logging
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO
from pcdsdevices.interface import BaseInterface
import time
logger = logging.getLogger(__name__)


class MPODApalisChannel(BaseInterface, Device):
    """
    MPODApalis Channel Object.

    Parameters
    ----------
    channel_prefix : str
        The EPICS base of the MPOD Channel. E.g.: `TMO:MPOD:01:M5:C6
    name : str
       A name to refer to the device.

    """
    voltage = Cpt(EpicsSignal, ':VoltageMeasure',
                  write_pv=':VoltageSet', kind='normal',
                  doc='MPOD Channel Voltage Measurement [V]')

    max_voltage = Cpt(EpicsSignalRO, ':VoltageNominal', kind='normal',
                      doc='MPOD Channel Maximum Voltage [V]')

    current = Cpt(EpicsSignal, ':CurrentMeasure',
                  write_pv=':CurrentSet', kind='normal',
                  doc='MPOD Channel Current Measure')

    max_current = Cpt(EpicsSignalRO, ':CurrentNominal', kind='normal',
                      doc='MPOD Channel Current Maximum')

    state = Cpt(EpicsSignal, ':isOn', write_pv=':Control:setOn',
                kind='normal', string=True,
                doc='MPOD Channel State [Off/On]')

    tab_component_names = True
    tab_whitelist = ['on', 'off',
                     'set_voltage', 'set_current']

    def __init__(self, channel_prefix, name='MPOD Channels', **kwargs):
        super().__init__(channel_prefix, name=name, **kwargs)

    def on(self):
        """Set mpod channel On."""
        self.state.put(1)

    def off(self):
        """Set mpod channel Off."""
        self.state.put(0)

    def set_voltage(self, voltage):
        """
        Set mpod channel voltage in V.
        Parameters
        ----------
        voltage : number
            Voltage in V.
        """
        self.voltage.put(voltage)

    def set_current(self, current_number):
        """
        Set mpod channel current in A.
        Parameters
        ----------
        current_number : number
            Current in A.
        """
        if current_number <= self.max_current:
            self.current.put(current_number)
        else:
            print('The maximal current limit is %g' % self.max_current)
            print('will set current limit to max')
            self.current.put(self.max_current)


class MPODApalisModule(BaseInterface, Device):

    """
    MPODApalis Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module. `TMO:MPOD:01:M6
    name : str
       A name to refer to the device.
    """

    temperature = Cpt(EpicsSignalRO, ':Temperature', kind='normal',
                      doc='MPOD Temperature [C]')

    clear_faults = Cpt(EpicsSignal, ':isEventActive',
                       write_pv=':Control:doClear',
                       kind='normal', string=True,
                       doc='Clears all MPOD module faults')

    def __init__(self, card_prefix, name='MPOD Module',
                 **kwargs):
        super().__init__(card_prefix, name=name, **kwargs)
    tab_component_names = True
    tab_whitelist = ['clr_evnts']

    def clr_evnts(self):
        self.clear_faults.put(1)


class MPODApalisModule4Channel(MPODApalisModule):
    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")


class MPODApalisModule8Channel(MPODApalisModule):
    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")
    c4 = Cpt(MPODApalisChannel, ":C4")
    c5 = Cpt(MPODApalisChannel, ":C5")
    c6 = Cpt(MPODApalisChannel, ":C6")
    c7 = Cpt(MPODApalisChannel, ":C7")


class MPODApalisModule16Channel(MPODApalisModule):
    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")
    c4 = Cpt(MPODApalisChannel, ":C4")
    c5 = Cpt(MPODApalisChannel, ":C5")
    c6 = Cpt(MPODApalisChannel, ":C6")
    c7 = Cpt(MPODApalisChannel, ":C7")
    c8 = Cpt(MPODApalisChannel, ":C8")
    c9 = Cpt(MPODApalisChannel, ":C9")
    c10 = Cpt(MPODApalisChannel, ":C10")
    c11 = Cpt(MPODApalisChannel, ":C11")
    c12 = Cpt(MPODApalisChannel, ":C12")
    c13 = Cpt(MPODApalisChannel, ":C13")
    c14 = Cpt(MPODApalisChannel, ":C14")
    c15 = Cpt(MPODApalisChannel, ":C15")


class MPODApalisModule24Channel(MPODApalisModule):
    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")
    c4 = Cpt(MPODApalisChannel, ":C4")
    c5 = Cpt(MPODApalisChannel, ":C5")
    c6 = Cpt(MPODApalisChannel, ":C6")
    c7 = Cpt(MPODApalisChannel, ":C7")
    c8 = Cpt(MPODApalisChannel, ":C8")
    c9 = Cpt(MPODApalisChannel, ":C9")
    c10 = Cpt(MPODApalisChannel, ":C10")
    c11 = Cpt(MPODApalisChannel, ":C11")
    c12 = Cpt(MPODApalisChannel, ":C12")
    c13 = Cpt(MPODApalisChannel, ":C13")
    c14 = Cpt(MPODApalisChannel, ":C14")
    c15 = Cpt(MPODApalisChannel, ":C15")
    c16 = Cpt(MPODApalisChannel, ":C16")
    c17 = Cpt(MPODApalisChannel, ":C17")
    c18 = Cpt(MPODApalisChannel, ":C18")
    c19 = Cpt(MPODApalisChannel, ":C19")
    c20 = Cpt(MPODApalisChannel, ":C20")
    c21 = Cpt(MPODApalisChannel, ":C21")
    c22 = Cpt(MPODApalisChannel, ":C22")
    c23 = Cpt(MPODApalisChannel, ":C23")


class MPODApalisCrate(BaseInterface, Device):

    """
    MPODApalis Crate Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Crate. `TMO:MPOD:01
    name : str
       A name to refer to the device.
    """

    power = Cpt(EpicsSignal, ':Crate:PowerOn',
                kind='normal', string=True,
                doc='Crate power status and control')

    def __init__(self, crate_prefix, name='MPOD',
                 **kwargs):
        super().__init__(crate_prefix, name=name, **kwargs)

    tab_component_names = True
    tab_whitelist = ['power']

    def power_cycle(self):
        self.power.put(0)
        time.sleep(5)
        self.power.put(1)
