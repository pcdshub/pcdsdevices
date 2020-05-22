# Hacky ophyd hotfix
from ophyd.device import Device

from ._version import get_versions


def __contains__(self, value):
    return value in self._OphydAttrList__internal_list()


Device.OphydAttrList.__contains__ = __contains__
del Device
del __contains__

__version__ = get_versions()['version']
del get_versions
