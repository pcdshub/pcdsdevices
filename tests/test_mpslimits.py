############
# Standard #
############
import time
import logging
from functools import partial

###############
# Third Party #
###############
import pytest
from ophyd import Device
from unittest.mock import Mock

##########
# Module #
##########
from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics.mps import MPS, mps_factory, MPSLimits, must_be_open_logic, must_know_position_logic

from .conftest import attr_wait_true


def fake_mps():

    mpsLimits = MPSLimits("TST:MPSA", "TST:MPSB")
    return mpsLimits


@using_fake_epics_pv

def test_mpsLimits_fault_test1_openLogic():
    mpsLimits = fake_mps()
    #Both mps_A and mps_B faulted, asserting MPSLimits should return False
    mpsLimits.mps_A.fault._read_pv.put(1)
    mpsLimits.mps_A.bypass._read_pv.put(0)   
    assert mpsLimits.mps_A.faulted
 
    mpsLimits.mps_B.fault._read_pv.put(1)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert mpsLimits.mps_B.faulted
    
    mpsLimits.logic = must_be_open_logic
    assert mpsLimits.faulted == False

@using_fake_epics_pv

def test_mpsLimits_fault_test1_positionLogic():
    mpsLimits = fake_mps()
    #Both mps_A and mps_B faulted, asserting MPSLimits should return False
    mpsLimits.mps_A.fault._read_pv.put(1)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert mpsLimits.mps_A.faulted

    mpsLimits.mps_B.fault._read_pv.put(1)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert mpsLimits.mps_B.faulted

    mpsLimits.logic = must_know_position_logic
    assert mpsLimits.faulted == False

@using_fake_epics_pv

def test_mpsLimits_fault_test2_openLogic():
    mpsLimits = fake_mps()
    #mps_A is faulted, mps_B is not so must_know_position_logic used
    mpsLimits.mps_A.fault._read_pv.put(1)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert mpsLimits.mps_A.faulted

    mpsLimits.mps_B.fault._read_pv.put(0)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert not mpsLimits.mps_B.faulted

    mpsLimits.logic = must_be_open_logic
    assert mpsLimits.faulted == False

@using_fake_epics_pv

def test_mpsLimits_fault_test2_positionLogic():
    mpsLimits = fake_mps()
    #mps_A is faulted, mps_B is not so must_know_position_logic used
    mpsLimits.mps_A.fault._read_pv.put(1)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert mpsLimits.mps_A.faulted

    mpsLimits.mps_B.fault._read_pv.put(0)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert not mpsLimits.mps_B.faulted

    mpsLimits.logic = must_know_position_logic
    assert mpsLimits.faulted



@using_fake_epics_pv

def test_mpsLimits_fault_test3_openLogic():
    mpsLimits = fake_mps()
    #Both mps_A and mps_B are not faulted, asserting MPSlimits should return false
    mpsLimits.mps_A.fault._read_pv.put(0)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert not mpsLimits.mps_A.faulted
    
    mpsLimits.mps_B.fault._read_pv.put(0)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert not mpsLimits.mps_B.faulted

    mpsLimits.logic = must_be_open_logic
    assert mpsLimits.faulted == False 


@using_fake_epics_pv

def test_mpsLimits_fault_test3_positionLogic():
    mpsLimits = fake_mps()
    #Both mps_A and mps_B are not faulted, asserting MPSlimits should return false
    mpsLimits.mps_A.fault._read_pv.put(0)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert not mpsLimits.mps_A.faulted

    mpsLimits.mps_B.fault._read_pv.put(0)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert not mpsLimits.mps_B.faulted

    mpsLimits.logic = must_know_position_logic
    assert mpsLimits.faulted == False


@using_fake_epics_pv

def test_mpsLimits_fault_test4_openLogic():

    mpsLimits = fake_mps()
    #mps_A is not faulted and mps_B is, asserting MPSlimits should call must_know_positions_logic
    mpsLimits.mps_A.fault._read_pv.put(0)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert not mpsLimits.mps_A.faulted

    mpsLimits.mps_B.fault._read_pv.put(1)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert mpsLimits.mps_B.faulted

    mpsLimits.logic = must_be_open_logic
    assert mpsLimits.faulted


@using_fake_epics_pv

def test_mpsLimits_fault_test4_positionLogic():

    mpsLimits = fake_mps()
    #mps_A is not faulted and mps_B is, asserting MPSlimits should call must_know_positions_logic
    mpsLimits.mps_A.fault._read_pv.put(0)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert not mpsLimits.mps_A.faulted

    mpsLimits.mps_B.fault._read_pv.put(1)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert mpsLimits.mps_B.faulted

    mpsLimits.logic = must_know_position_logic
    assert mpsLimits.faulted


 

