from ophyd import setup_ophyd
from ._version import get_versions

setup_ophyd()
del setup_ophyd
__version__ = get_versions()['version']
del get_versions
