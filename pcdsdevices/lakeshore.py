"""
Classes for lakeshore temperature controller
"""
import logging
import subprocess

from ophyd import Component as Cpt
from ophyd import FormattedComponent as FCpt
from ophyd import Device, EpicsSignal, EpicsSignaRO, EpicsSignalWithRBV

from .interface import BaseInterface

logger = loggin.getLogger(__name__)

class Lakeshore336(Device):
	"""
	two loops
	4 temperature sensors 
	also include device control mode
	"""


	# two loops
	temp_loop_1 = Cpt(EpicsSignal, 'GET_SOLL_{self.channel}', write_pv = 'PUT_SOLL_{self.channel}', kind = 'normal')
    temp_loop_2 = Cpt(EpicsSignal, 'GET_SOLL_{self.channel}', write_pv = 'PUT_SOLL_{self.channel}', kind = 'normal')

    # 4 temperature sensors
    temp_A = Cpt(TemperatureSensor, channel = 'A', kind = 'normal')
    temp_B = Cpt(TemperatureSensor, channel = 'B', kind = 'normal')
    temp_C = Cpt(TemperatureSensor, channel = 'C', kind = 'normal')
    temp_D = Cpt(TemperatureSensor, channel = 'D', kind = 'normal')

    # device control mode
    device_control = Cpt(HeaterControlMode, kind = 'normal')

class Loop():
	pass

class Heater(Device):
	# note: do not hardcode channel
	# should take in channel input, hardcode kind to normal
	
	range = Cpt(HeaterState, channel = '1', kind = 'normal')


class HeaterState(StatePositioner):
	"""
    HeaterState Channel Object.

    Parameters
    ----------
    channel_prefix : str
        The EPICS base of the HeaterState Channel. E.g.: ``
    card_prefix : str, optional
        The EPICS base of the MPOD Module. `XPP:R39:MPD:MOD:10`
    """
	range = Cpt(EpicsSignal, 'GET_RANGE_{self.channel}',
            write_pv = 'PUT_RANGE_{self.channel}', kind = 'normal', doc = 'heater range')
	state = Cpt(EpicsSignalRO, 'GET_HTRSTAT_{self.channel}', kind = 'normal')

	_unknown = False
	states_list = ['Off', 'Low', 'Medium', 'High']
	# insert tab white list

	def __init__(self, prefix, channel, **kwargs):
		self.channel = channel
		super().__init__(prefix, **kwargs)

class TemperatureSensor(BaseInterface, Device):
    input_name = Cpt(EpicsSignalRO, 'GET_INAME_{self.channel}', kind =
            'config')
    temp = Cpt(EpicsSignalRO, 'GET_TEMP_{self.channel}', kind = 'normal')
    units = Cpt(EpicsSignal, 'GET_UNITS_{self.channel}', write_pv =
            'PUT_UNITS_{self.channel}', kind = 'normal')
    sensor_type = Cpt(EpicsSignalRO, 'GET_SENSOR_{self.channel}', kind =
            'normal')

    def __init__(self, prefix, channel, **kwargs):
        self.channel = channel
        super().__init__(prefix, **kwargs)



class HeaterControlMode(StatePositioner):
	"""
	Class for Heater control 
	"""
	mode = Cpt(EpicsSignal, 'GET_MODE', write_pv = 'PUT_MODE', kind = 'normal', doc = 'control mode')
    _unknown = False
	states_list = ['Local, Remote, Rem/Lock']
	tab_component_name = True







