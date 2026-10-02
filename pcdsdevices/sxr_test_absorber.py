"""
Backwards compatibility:
ST1K0 used to be the ST1K4 sxr test absorber.

This file may be removed in a future release.
"""

import warnings

from .stopper import ST1K0

warnings.warn(
    "pcdsdevices.sxr_test_absorber.SxrTestAborber is deprecated and is now pcdsdevices.stopper.ST1K0",
    DeprecationWarning,
    stacklevel=2,
)

SxrTestAbsorber = ST1K0
ST3K4AutoError = RuntimeError
