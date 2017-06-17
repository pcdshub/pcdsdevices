from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

#import logging # NOQA
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

from .device import Device # NOQA

# Let the submodules decide what to push up to the top level
# Assume ImportError means that we can't use the optional submodule
try:
    from .epics import * # NOQA
except ImportError:
    pass
