from .imsmotor import IMSMotor
from .valve    import GateValve

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
