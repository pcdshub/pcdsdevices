import warnings

from .interface import *  # NOQA

warnings.warn("pcdsdevices.mv_interface is deprecated and will be removed in "
              "a future release. Please use pcdsdevices.interface instead.",
              DeprecationWarning)
