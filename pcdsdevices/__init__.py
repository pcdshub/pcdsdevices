from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

try:
    from .epics import *
except ImportError:
    pass
