############
# Standard #
############
import logging

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pcdsdevices.epics import state
from conftest import requires_epics

logger = logging.getLogger(__name__)

@requires_epics
@pytest.mark.timeout(3)
def test_statesrecord_class_reads():
    """
    Instantiate one if we can and make sure value makes sense.
    """
    inout = state.InOutStates("XCS:SB2:PIM6:DIODE")
    assert(inout.value in ("IN", "OUT", "Unknown"))
