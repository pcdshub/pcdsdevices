"""
Basic Beryllium Lens XFLS

The scope of this module is picking a lens, not focusing or aligning the
lenses. This will be expanded in the future.
"""
from .inout import InOutRecordPositioner


# Most places
class XFLS(InOutRecordPositioner):
    """
    XRay Focusing Lens (Be)

    This is the simple version where the lens positions are named by number.
    """
    states_list = ['LENS1', 'LENS2', 'LENS3', 'OUT']
    in_states = ['LENS1', 'LENS2', 'LENS3']
    # TODO: Choose a transmission for a generic lens


# MFX DIA
# CXI DG2
class XFLS2(XFLS):
    """
    XRay Focusing Lens (Be)

    These are the stacks with common names on their states and state config PVs
    that show the focusing config
    """
    states_list = ['6K70', '7K50', '9K45', 'OUT']
    in_states = ['6K70', '7K50', '9K45']


# CXI DS1
class XFLS3(XFLS):
    """
    XRay Focusing Lens (Be)

    This is the stack in CXI with a screwed up IOC. The states list are
    numbered by lens, but the config PVs are all over the place.

    This currently behaves no differently than XFLS, but when we add in the
    state config these values will matter. I'm saving them here for later.
    """
    # Upper/lower case intentional
    _config_states = ['6K70', '7k45', '9k50']
