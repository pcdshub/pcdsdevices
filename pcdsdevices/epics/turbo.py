from ophyd import Device, EpicsSignal
from ophyd import Component as C

"""
Turbo pumps device class for PCDS

This class will allow access to set the value for the turbo pumps in order to
programatically vent the chamber.0 indicates Low (OFF), 1 indicates High (ON)

"""


class Turbo(Device):

    """
    Base turbo class for CXI turbo pumps.

    Parameters   
    ----------
 
    prefix: str
        The EPICS base pv to use.
        Expected format: {hutch}:{stand}:{device_abbrv}:{number}

    name: str
        The name of the turbo pump

    """

    turboStart = C(EpicsSignal, ':START_SW')
    turboRun = C(EpicsSignal, ':RUN_SW')

    def selectMode(self, *argv):
       
        """

        Shortcut to allow user to change the status of the Turbo device. 

        Accepted arguments: 0,1

        selectMode(0) will turn off the turbo device.
        selectMode(1) will turn the turbo device on.

        """

        for arg in argv:
            if arg == 0:
                try:
                    self.turboStart.put(value=0)
                except TimeoutError:

                    try:
                        self.turboRun.put(value=0)
                    except TimeoutError:
                        print("Error with Device - check prefix")
           
            elif arg == 1: 
                try:
                    self.turboStart.put(value=1)
                except TimeoutError:
                    try:
                        self.turboRun.put(value=1)
                    except TimeoutError:
                        print("Error with device - check prefix")       
       
            else:
                print("Only valid arguments are 0(off) & 1(on)") 
   
    def turnOff(self):

        """

        Shortcut to quickly turn off the selected turbo device

        """

        try:
            self.turboStart.put(value=0)
        except TimeoutError:
            try:
                self.turboRun.put(value=0)
            except TimeoutError:
                print("Error with Device - check prefix")

    def turnOn(self):

        """

        Shortcut to quickly turn on the selected turbo device"

        """

        try:
            self.turboStart.put(value=1)
        except TimeoutError:
            try:
                self.turboRun.put(value=1)
            except TimeoutError:
                print("Error with Device - check prefix")
