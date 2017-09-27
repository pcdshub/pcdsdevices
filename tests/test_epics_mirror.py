############
# Standard #
############

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pcdsdevices.epics.mirror import OffsetMirror
from pcdsdevices.sim.pv       import using_fake_epics_pv

@using_fake_epics_pv
@pytest.fixture(scope='function')
def branching_mirror():
    m = OffsetMirror("MIRR:TST:M1H", "GANTRY:TST:M1H",
                     mps="MIRR:M1H:MPS", state_prefix="TST:M1H",
                     in_lines=['MFX', 'MEC'], out_lines= ['CXI'])
    return m

@using_fake_epics_pv
@pytest.fixture(scope='function')
def inline_mirror():
    m = OffsetMirror("MIRR:TST:M1H", "GANTRY:TST:M1H",
                     mps="MIRR:M1H:MPS", db_info={'beamline' : 'FEE'})
    return m

@using_fake_epics_pv
def test_branching_mirror(branching_mirror):
    assert branching_mirror.branches == ['MFX', 'MEC', 'CXI']
    #Unknown
    assert branching_mirror.destination == []
    #Inserted
    branching_mirror.state.in_state.at_state._read_pv.put(1)
    assert branching_mirror.destination == ['MFX', 'MEC']
    #Removed
    branching_mirror.state.out_state.at_state._read_pv.put(1)
    branching_mirror.state.in_state.at_state._read_pv.put(0)
    assert branching_mirror.destination == ['CXI']

@using_fake_epics_pv
def test_inline_mirror(inline_mirror):
    assert inline_mirror.branches == ['FEE']
    assert inline_mirror.destination == ['FEE']
