
"""
Pneumatic Classes.

This Module contains all the classes relating to Pneumatic Actuators 
"""

from ophyd import Component as Cpt
from ophyd import EpicsSignalRO, EpicsSignal
from ophyd.device import Device

class BeckhoffPneumatic(Device):
	"""
	Class containing basic Beckhoff Pneumatic support
	"""

	#readouts
	limit_switch_in = Cpt(EpicsSignalRO, ':PLC:bInLimitSwitch')
	limit_switch_out = Cpt(EpicsSignalRO, ':PLC:bOutLimitSwitch')

	interlock_ok = Cpt(EpicsSignalRO, 'bInterlockOK')
	insert_ok = Cpt(EpicsSignalRO, 'bInsertEnable')
	retract_ok = Cpt(EpicsSignalRO, 'bretractEnable')

	
	retract_status = Cpt(EpicsSignalRO, ':bRetractDigitalOutput')
	insert_status = Cpt(EpicsSignalRO, ':bInsertDigitalOutput')

	busy = Cpt(EpicsSignalRO, ':bBusy')
	done = Cpt(EpicsSignalRO, ':bDone')
	error = Cpt(EpicsSignalRO, ':PLC:bError')
	error_id = Cpt(EpicsSignalRO, ':PLC:nErrorId')
	error_string = Cpt(EpicsSignalRO, ':PLC:sErrorMessage')
	position_state = Cpt(EpicsSignalRO, ':nPositionState')
    
	reset = Cpt(EpicsSignal, ':bReset')
	



