import warnings

from .device import *  # NOQA

warnings.warn(
    "pcdsdevices.component is deprecated and will be removed in a "
    "future release. Please use pcdsdevices.device."
    )
