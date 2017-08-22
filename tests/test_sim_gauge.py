############
# Standard #
############
import time
from collections import OrderedDict

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pcdsdevices.sim import gauge

tmo = 10

# GaugeBase

@pytest.mark.timeout(tmo)
def test_GaugeBase_instantiates():
    assert(gauge.GaugeBase("TEST"))

@pytest.mark.timeout(tmo)
def test_GaugeBase_runs_ophyd_functions():
    g = gauge.GaugeBase("TEST")
    assert(isinstance(g.read(), OrderedDict))
    assert(isinstance(g.describe(), OrderedDict))
    assert(isinstance(g.describe_configuration(), OrderedDict))
    assert(isinstance(g.read_configuration(), OrderedDict))
    
# Pirani

@pytest.mark.timeout(tmo)
def test_Pirani_instantiates():
    assert(gauge.Pirani("TEST"))

@pytest.mark.timeout(tmo)
def test_Pirani_runs_ophyd_functions():
    g = gauge.Pirani("TEST")
    assert(isinstance(g.read(), OrderedDict))
    assert(isinstance(g.describe(), OrderedDict))
    assert(isinstance(g.describe_configuration(), OrderedDict))
    assert(isinstance(g.read_configuration(), OrderedDict))

# Cold Cathode

@pytest.mark.timeout(tmo)
def test_ColdCathode_instantiates():
    assert(gauge.ColdCathode("TEST"))

@pytest.mark.timeout(tmo)
def test_ColdCathode_runs_ophyd_functions():
    g = gauge.ColdCathode("TEST")
    assert(isinstance(g.read(), OrderedDict))
    assert(isinstance(g.describe(), OrderedDict))
    assert(isinstance(g.describe_configuration(), OrderedDict))
    assert(isinstance(g.read_configuration(), OrderedDict))

@pytest.mark.timeout(tmo)
def test_ColdCathode_correctly_names_pirani():
    g = gauge.ColdCathode("VGCC:TST:01")
    assert(g.pirani.prefix == "VGCP:TST:01")
    
