"""
Basic Beryllium Lens XFLS

The scope of this module is picking a lens, not focusing or aligning the
lenses. This will be expanded in the future.
"""
from .inout import InOutRecordPositioner


class XFLS(InOutRecordPositioner):
    """
    XRay Focusing Lens (Be)

    This is the simple version where the lens positions are named by number.
    """
    states_list = ['LENS1', 'LENS2', 'LENS3', 'OUT']
    in_states = ['LENS1', 'LENS2', 'LENS3']
    # TODO: Choose a transmission for a generic lens
