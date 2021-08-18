import logging
import time

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from pcdsdevices.interface import BaseInterface

from .device import GroupDevice

logger = logging.getLogger(__name__)


class MPODApalisChannel(BaseInterface, Device):
    """
    MPODApalis Channel Object.

    Parameters
    ----------
    channel_prefix : str
        The EPICS base of the MPOD Channel, e.g. 'TMO:MPOD:01:M6:C6'.
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

    def on(self):
        """Set mpod channel On."""
        self.state.put(1)

    def off(self):
        """Set mpod channel Off."""
        self.state.put(0)

    def set_voltage(self, voltage_number):
        """
        Set mpod channel voltage in V.
        Parameters
        ----------
        voltage_number : number
            Voltage in V.
        """
        max_voltage = self.max_voltage.get()

        if voltage_number <= max_voltage:
            self.voltage.put(voltage_number)
        else:
            self.voltage.put(max_voltage)
            logger.warning('The maximal voltage is %g will set voltage to %g'
                           % (max_voltage, max_voltage))

    def set_current(self, current_number):
        """
        Set mpod channel current in A.
        Parameters
        ----------
        current_number : number
            Current in A.
        """

        max_current = self.max_current.get()

        if current_number <= max_current:
            self.current.put(current_number)
        else:
            self.current.put(max_current)
            logger.warning('The maximal current is %g will set current to %g'
                           % (max_current, max_current))


class MPODApalisModule(BaseInterface, GroupDevice):

    """
    MPODApalis Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    voltage_ramp_speed = Cpt(EpicsSignal, ':VoltageRampSpeed', kind='normal',
                             doc='MPOD module Voltage Ramp Rate [%/sec*Vnom]')

    current_ramp_speed = Cpt(EpicsSignal, ':CurrentRampSpeed', kind='normal',
                             doc='MPOD module current Ramp  Rate [%/sec*Inom]')

    temperature = Cpt(EpicsSignalRO, ':Temperature', kind='normal',
                      doc='MPOD Temperature [C]')

    faults = Cpt(EpicsSignal, ':isEventActive',
                 write_pv=':Control:doClear',
                 kind='normal', string=True,
                 doc='Clears all MPOD module faults')

    tab_component_names = True
    tab_whitelist = ['clear_faults', 'set_voltage_ramp_speed',
                     'set_current_ramp_speed']

    def clear_faults(self):
        """Clears all module faults"""
        self.faults.put(1)

    def set_voltage_ramp_speed(self, ramp_speed):
        """
        Set the voltage ramp speed in %/sec*Vnom.

        It sets the voltage ramp speed for the entire card.

        Parameters
        ----------
        ramp_speed : number
            Voltage rise rate [%/sec*Vnom].
        """
        self.voltage_ramp_speed.put(ramp_speed)

    def set_current_ramp_speed(self, ramp_speed):
        """
        Set the current ramp speed in %/sec*Inom.

        It sets the current ramp speed for the entire card.

        Parameters
        ----------
        ramp_speed : number
            Current ramp speed [%/sec*Vnom].
        """
        self.current_ramp_speed.put(ramp_speed)


class MPODApalisModule4Channel(MPODApalisModule):

    """
    MPODApalis 4 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")


class MPODApalisModule8Channel(MPODApalisModule):

    """
    MPODApalis 8 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")
    c4 = Cpt(MPODApalisChannel, ":C4")
    c5 = Cpt(MPODApalisChannel, ":C5")
    c6 = Cpt(MPODApalisChannel, ":C6")
    c7 = Cpt(MPODApalisChannel, ":C7")


class MPODApalisModule16Channel(MPODApalisModule):

    """
    MPODApalis 16 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

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

    """
    MPODApalis 24 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

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
        The EPICS base of the MPOD Crate, e.g. 'TMO:MPOD:01'.
    name : str
        A name to refer to the device.
    """

    power = Cpt(EpicsSignal, ':Crate:PowerOn',
                kind='normal', string=True,
                doc='Crate power status and control')

    tab_component_names = True
    tab_whitelist = ['power']

    def power_cycle(self):
        """
        Function used to power cycle the MPOD crate
        """
        self.power.put(0)
        time.sleep(5)
        self.power.put(1)
